from django.urls import path
from .views import CreateOrderAPIView, VerifyPaymentAPIView

urlpatterns = [
    path("create-order/", CreateOrderAPIView.as_view()),
    path("verify-payment/", VerifyPaymentAPIView.as_view()),
]
