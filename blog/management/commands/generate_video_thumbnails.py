
from django.core.management.base import BaseCommand
from blog.models import VideoPost
from blog.video_utils import extract_video_thumbnail, generate_thumbnail_filename


class Command(BaseCommand):
    help = "Generate thumbnails for videos without cover images"

    def handle(self, *args, **options):
        videos_without_cover = VideoPost.objects.filter(cover_image__isnull=True) | VideoPost.objects.filter(cover_image="")
        count = videos_without_cover.count()
        
        self.stdout.write(f"Found {count} videos without cover images")
        
        success_count = 0
        for video in videos_without_cover:
            if video.video_file:
                self.stdout.write(f"Processing: {video.title or video.get_video_filename()}")
                
                thumbnail = extract_video_thumbnail(video.video_file)
                if thumbnail:
                    thumbnail_filename = generate_thumbnail_filename(video.video_file.name)
                    video.cover_image.save(thumbnail_filename, thumbnail, save=True)
                    success_count += 1
                    self.stdout.write(self.style.SUCCESS(f"  ✓ Thumbnail generated"))
                else:
                    self.stdout.write(self.style.ERROR(f"  ✗ Failed to extract thumbnail"))
        
        self.stdout.write(self.style.SUCCESS(f"Completed: {success_count}/{count} thumbnails generated"))
