from django.forms import ValidationError
from django.shortcuts import render
from rest_framework import viewsets, permissions, status, generics
from .permissions import IsInstructorOrReadOnly, IsStudent, CanViewLesson
from .models import Course, Enrollment, Lesson, LessonProgress
from .serializers import CourseSerializer, EnrollmentSerializer, LessonSerializer, LessonProgressSerializer
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework.views import APIView
from payments.models import Payment
from django.db.models import Count, Sum
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model
from rest_framework.parsers import MultiPartParser, FormParser
# Create your views here.

User = get_user_model()

class CourseViewSet(viewsets.ModelViewSet):
    serializer_class = CourseSerializer
    def get_permissions(self):
        if self.request.method == "DELETE":
            return [IsAuthenticated()]
        return [IsAuthenticatedOrReadOnly(), IsInstructorOrReadOnly()]

    def get_queryset(self):
        user = self.request.user

        if user.role == "instructor":
            return Course.objects.filter(instructor=user)

        return Course.objects.all()

    def perform_create(self, serializer):
        serializer.save(instructor=self.request.user)

    def destroy(self, request, *args, **kwargs):
        course = self.get_object()

    # Admin can delete any course
        if request.user.role == "admin":
            return super().destroy(request, *args, **kwargs)

    # Instructor can delete their own course
        if request.user.role == "instructor" and course.instructor == request.user:
            return super().destroy(request, *args, **kwargs)

        raise PermissionDenied("You cannot delete this course.")

class EnrollmentViewset(viewsets.ModelViewSet):
    serializer_class = EnrollmentSerializer
    permission_classes = [IsAuthenticated,IsStudent]

    def get_queryset(self):
        return Enrollment.objects.filter(student = self.request.user).select_related('course')
    
    def create(self, request, *args, **kwargs):
        course_id = request.data.get('course_id')

        if not course_id:
            raise ValidationError(
                {"detail": "Course ID required"},
            )
        
        try:
            course = Course.objects.get(id=course_id)
        except Course.DoesNotExist:
            return Response({"detail": "Course not found"}, status=404)


        if Enrollment.objects.filter(
            student= request.user,
             course=course
        ).exists():
            return Response(
                {'detail': "Already enrolled" },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if course.price > 0:
            return Response(
            {"detail": "Paid course. Please complete payment."},
            status=status.HTTP_400_BAD_REQUEST
        )
        
        serializer = self.get_serializer(
           data={"course_id": course_id})
        
        serializer.is_valid(raise_exception = True)
        serializer.save(student=request.user)

        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
class LessonViewset(viewsets.ModelViewSet):
    serializer_class=LessonSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    def get_queryset(self):
        user = self.request.user
        course_id = self.request.query_params.get("course")

        queryset = Lesson.objects.all()

        if course_id:
            queryset = queryset.filter(course_id=course_id)

        if user.role == 'instructor':
            return queryset.filter(course__instructor=user)
        
        return queryset
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context
    
    def perform_create(self, serializer):
        course = serializer.validated_data["course"]
        if course.instructor != self.request.user:
            raise PermissionDenied("You cannot add lessons to a course you don't own.")
        serializer.save()

    def get_permissions(self):
        if self.request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            return [IsInstructorOrReadOnly()]
        return [CanViewLesson()]

class LessonProgressViewSet(viewsets.ModelViewSet):
    serializer_class = LessonProgressSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = LessonProgress.objects.filter(student=self.request.user)

        lesson_id = self.request.query_params.get("lesson")
        if lesson_id:
            queryset = queryset.filter(lesson_id=lesson_id)

        return queryset
    def perform_create(self, serializer):
        serializer.save(student=self.request.user, completed=False)

class InstructorStatsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        instructor = request.user

        courses = Course.objects.filter(instructor=instructor)

        total_courses = courses.count()

        total_students = Enrollment.objects.filter(
            course__in=courses
        ).values("student").distinct().count()

        last_30_days = timezone.now() - timedelta(days=30)

        new_students = Enrollment.objects.filter(
            course__in=courses,
            enrolled_at__gte=last_30_days
        ).values("student").distinct().count()

        total_revenue = (
         Payment.objects.filter(
         course__in=courses,
         status="paid"
        ).aggregate(total=Sum("amount"))["total"] or 0
        ) / 100


        course_data = []
        for course in courses:
            students = Enrollment.objects.filter(course=course).count()
            revenue = (
                Payment.objects.filter(
                course=course,
                status="paid"
            ).aggregate(total=Sum("amount"))["total"] or 0
            ) / 100


            course_data.append({
                "id": course.id,
                "title": course.title,
                "students": students,
                "revenue": revenue,
            })

        latest_enrollments = Enrollment.objects.filter(
            course__in=courses
        ).select_related("student", "course").order_by("-enrolled_at")[:6]

        latest = [
            {
                "student": e.student.username,
                "course": e.course.title,
                "date": e.enrolled_at.strftime("%d %b %Y"),
            }
            for e in latest_enrollments
        ]

        return Response({
            "total_courses": total_courses,
            "total_students": total_students,
            "new_students": new_students,
            "total_revenue": total_revenue,
            "courses": course_data,
            "latest_enrollments": latest,
        })
    
class AdminStatsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != "admin":
            return Response({"detail": "Unauthorized"}, status=403)
        
        students = User.objects.filter(role="student").values(
            "id", "username", "email", "date_joined"
        )

        instructors = User.objects.filter(role="instructor").values(
            "id", "username", "email", "date_joined"
        )

        total_users = User.objects.count()
        total_students = students.count()
        total_instructors = instructors.count()

        total_courses = Course.objects.count()
        total_enrollments = Enrollment.objects.count()

        total_revenue = (
            Payment.objects.filter(status="paid")
            .aggregate(total=Sum("amount"))["total"] or 0
        ) / 100

        last_7_days = timezone.now() - timedelta(days=7)

        new_users = User.objects.filter(date_joined__gte=last_7_days).count()
        new_enrollments = Enrollment.objects.filter(enrolled_at__gte=last_7_days).count()

        return Response({
            "students": students,
            "instructors": instructors,
            "total_users": total_users,
            "total_students": total_students,
            "total_instructors": total_instructors,
            "total_courses": total_courses,
            "total_enrollments": total_enrollments,
            "total_revenue": total_revenue,
            "new_users": new_users,
            "new_enrollments": new_enrollments,
        })
    def delete(self, request, user_id):
        if request.user.role != "admin":
            return Response({"detail": "Unauthorized"}, status=403)

        try:
            user = User.objects.get(id=user_id)
            user.delete()
            return Response({"detail": "User deleted"})
        except User.DoesNotExist:
            return Response({"detail": "User not found"}, status=404)
    