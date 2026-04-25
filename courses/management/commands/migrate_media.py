import os
import cloudinary.uploader
from django.core.management.base import BaseCommand
from django.conf import settings
from courses.models import Course, Lesson


class Command(BaseCommand):
    help = "Migrate local media files to Cloudinary"

    def handle(self, *args, **kwargs):
        self.stdout.write("Migrating course thumbnails...")

        # --------------------------
        # Course thumbnail migration
        # --------------------------
        for course in Course.objects.all():
            if course.thumbnail:
                file_path = os.path.join(settings.MEDIA_ROOT, course.thumbnail.name)

                if os.path.exists(file_path):
                    try:
                        response = cloudinary.uploader.upload(
                            file_path,
                            resource_type="image"
                        )
                        course.thumbnail = response["secure_url"]
                        course.save()
                        self.stdout.write(f"Uploaded thumbnail: {course.title}")
                    except Exception as e:
                        self.stdout.write(f"Thumbnail failed: {course.title} → {e}")
                else:
                    self.stdout.write(f"Thumbnail missing: {course.title}")

        self.stdout.write("Migrating lesson files...")

        # --------------------------
        # Lesson video/resource migration
        # --------------------------
        for lesson in Lesson.objects.all():

            # ---- Video ----
            if lesson.video:
                file_path = os.path.join(settings.MEDIA_ROOT, lesson.video.name)

                if os.path.exists(file_path):
                    try:
                        response = cloudinary.uploader.upload(
                            file_path,
                            resource_type="video"
                        )
                        lesson.video = response["secure_url"]
                        lesson.save()
                        self.stdout.write(f"Video uploaded: {lesson.title}")
                    except Exception as e:
                        self.stdout.write(f"Video failed: {lesson.title} → {e}")
                else:
                    self.stdout.writ
