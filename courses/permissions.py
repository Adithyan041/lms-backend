from rest_framework.permissions import BasePermission, SAFE_METHODS
from rest_framework.permissions import BasePermission
from courses.models import Enrollment

class IsInstructorOrReadOnly(BasePermission):


    def has_permission(self, request, view):
        # Only instructors can POST
        if request.method == "POST":
            return request.user.is_authenticated and request.user.role=='instructor'
        # Everyone else can access GET
        return True
    
    def has_object_permission(self, request, view, obj):
        # Allow read-only methods: GET, HEAD, OPTIONS
        if request.method in SAFE_METHODS:
            return True
        
        if hasattr(obj, "instructor"):
            return obj.instructor == request.user

        # If object is Lesson
        if hasattr(obj, "course"):
            return obj.course.instructor == request.user

        return False

class IsStudent(BasePermission):
    def has_permission(self, request, view):
        return(
            request.user.is_authenticated and
            request.user.role == 'student'
        )
    
class CanViewLesson(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Instructor can view their own course lessons
        if request.user.role == 'instructor':
            return obj.course.instructor == request.user

        # Student can view only if enrolled
        return Enrollment.objects.filter(
            student=request.user,
            course=obj.course
        ).exists()
    
class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.role == "admin")
