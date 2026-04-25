from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import QuizViewSet, SubmitQuizView

router = DefaultRouter()
router.register(r'',QuizViewSet)

urlpatterns = router.urls + [
    path('<int:quiz_id>/submit/',SubmitQuizView.as_view()),
]