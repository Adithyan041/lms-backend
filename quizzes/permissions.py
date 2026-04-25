from rest_framework.permissions import BasePermission
from courses.models import Enrollment

class IsEnrolledStudent(BasePermission):
    def has_permission(self, request, view):
        quiz = view.get_quiz()
        return Enrollment.objects.filter(
            student= request.user,
            course=quiz.course
        ).exists()