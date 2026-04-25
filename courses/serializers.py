from rest_framework import serializers
from .models import Course, Enrollment, Lesson, LessonProgress


class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = [
            'id',
            'title',
            'description',
            'category',
            'price',
            'instructor',
            'thumbnail',
            'created_at'
        ]
        read_only_fields = ['instructor', 'created_at']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.thumbnail:
            data['thumbnail'] = instance.thumbnail.url
        return data


class EnrollmentSerializer(serializers.ModelSerializer):
    course = CourseSerializer(read_only=True)
    course_id = serializers.PrimaryKeyRelatedField(
        queryset=Course.objects.all(),
        source="course",
        write_only=True,
    )

    class Meta:
        model = Enrollment
        fields = ["id", "course", "course_id", "enrolled_at"]
        read_only_fields = ["student", "enrolled_at"]


class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = [
            'id',
            'course',
            'title',
            'content',
            'video',
            'resource',
            'order',
            'created_at'
        ]
        extra_kwargs = {'course': {'required': False}}

    
    def get_locked(self, obj):
        request = self.context.get("request")

        if not request or not request.user.is_authenticated:
            return True

        user = request.user

        # Instructor can access
        if user.role == "instructor" and obj.course.instructor == user:
            return False

        # Check enrollment
        from .models import Enrollment
        enrolled = Enrollment.objects.filter(
            student=user,
            course=obj.course
        ).exists()

        return not enrolled

    def to_representation(self, instance):
        data = super().to_representation(instance)

        if instance.video:
            data['video'] = instance.video.url

        if instance.resource:
            data['resource'] = instance.resource.url

        return data
    
class LessonProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = LessonProgress
        fields = ['id', 'lesson', 'student', 'completed', 'completed_at']
        read_only_fields = ['student', 'completed_at']
