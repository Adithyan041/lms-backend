from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
# Create your views here.

from .models import Quiz,Question, QuizAttempt
from .serializers import QuizSerializer
from courses.models import Enrollment

class QuizViewSet(viewsets.ModelViewSet):
    queryset = Quiz.objects.all()
    serializer_class = QuizSerializer
    Permission_classes=[IsAuthenticated]

class SubmitQuizView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, quiz_id):
        quiz = Quiz.objects.get(id=quiz_id)

        if not Enrollment.objects.filter(     # Check enrollment
            student=request.user,
            course = quiz.course
        ).exists():
            return Response(
                {'detail': 'Not enrolled'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if QuizAttempt.objects.filter(  # Prevent multiple attempts
            student=request.user,
            quiz=quiz
        ).exists():
            return Response(
                {"detail": "Already attempted"},
                status=status.HTTP_400_BAD_REQUEST
            )
        answers = request.data.get('answers',{})
        score = 0

        for question in quiz.questions.all():
            selected = answers.get(str(question.id))
            if selected == question.correct_option:
                score += question.marks

        QuizAttempt.objects.create(
            student=request.user,
            quiz=quiz,
            score=score
        )

        return Response({
            "score": score,
            "total": quiz.total_marks
        })