import razorpay
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.conf import settings
from .razorpay_client import client
from courses.models import Course, Enrollment
from .models import Payment


client = razorpay.Client(auth=(
    settings.RAZORPAY_KEY_ID,
    settings.RAZORPAY_KEY_SECRET
))

class CreateOrderAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        course_id = request.data.get("course_id")
       
        try:
            course = Course.objects.get(id=course_id)
        except Course.DoesNotExist:
            return Response({"detail": "Course not found"}, status=404)

        # Already enrolled?
        if Enrollment.objects.filter(student=request.user, course=course).exists():
            return Response({"detail": "Already enrolled"}, status=400)

        amount = int(course.price * 100)  # INR → paise

        order = client.order.create({
            "amount": amount,
            "currency": "INR",
            "payment_capture": 1
        })

        payment = Payment.objects.create(
            user=request.user,
            course=course,
            razorpay_order_id=order["id"],
            amount=amount,
            status="created"
        )

        return Response({
            "order_id": order["id"],
            "amount": amount,
            "key": settings.RAZORPAY_KEY_ID,
            "course": course.title
        })


class VerifyPaymentAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data

        try:
            client.utility.verify_payment_signature(data)
        except:
            return Response({"detail": "Payment verification failed"}, status=400)

        payment = Payment.objects.get(razorpay_order_id=data["razorpay_order_id"])

        payment.razorpay_payment_id = data["razorpay_payment_id"]
        payment.razorpay_signature = data["razorpay_signature"]
        payment.status = "paid"
        payment.save()

        enrollment, created = Enrollment.objects.get_or_create(
            student=request.user,
            course=payment.course
        )

        enrollment.is_paid = True
        enrollment.save()

        return Response({"detail": "Payment verified & enrolled"})