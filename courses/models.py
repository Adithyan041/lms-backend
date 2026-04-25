from django.db import models
# from accounts.models import User
from django.conf import settings
from django.utils import timezone
from cloudinary.models import CloudinaryField
# Create your models here.
User = settings.AUTH_USER_MODEL
class Course(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    category = models.CharField(max_length=100, blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    instructor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='courses')
    thumbnail = CloudinaryField('image', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Enrollment(models.Model):
    student = models.ForeignKey(User, on_delete = models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(Course, on_delete = models.CASCADE, related_name="enrollments")
    enrolled_at = models.DateTimeField(auto_now_add = True )
    is_paid = models.BooleanField(default=False)

    class Meta:
        unique_together = ('student','course')

    def __str__(self):
        return f"{self.student} enrolled in {self.course}"
    
class Lesson(models.Model):
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='lessons'
    )
    title = models.CharField(max_length=255)
    video = CloudinaryField(resource_type="video", blank=True, null=True)
    resource = CloudinaryField(resource_type="raw", blank=True, null=True)
    content = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.course.title}-{self.title}"
    
class LessonProgress(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="progress")
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('lesson', 'student')
    def save(self, *args, **kwargs):
        if self.completed and self.completed_at is None:
            self.completed_at = timezone.now()
        super().save(*args, **kwargs)
