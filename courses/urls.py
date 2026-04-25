from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import CourseViewSet, EnrollmentViewset, LessonViewset, LessonProgressViewSet, InstructorStatsAPIView,AdminStatsAPIView 

router = DefaultRouter()
router.register(r'courses', CourseViewSet, basename='courses')
router.register(r'enrollments', EnrollmentViewset, basename='enrollments')
router.register(r'lessons', LessonViewset, basename='lessons')
router.register(r'progress', LessonProgressViewSet, basename='progress')

urlpatterns = router.urls + [
    path("instructor/stats/", InstructorStatsAPIView.as_view(), name="instructor-stats"),
    path("admin/stats/", AdminStatsAPIView.as_view()),
]