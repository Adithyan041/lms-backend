from django.urls import path
from .views import AdminStatsAPIView

urlpatterns = [
    path("stats/", AdminStatsAPIView.as_view(), name="admin-stats"),
    path("users/", AdminStatsAPIView.as_view()),
    path("users/<int:user_id>/", AdminStatsAPIView.as_view()),
]
