"""
Video processing utilities for extracting thumbnails and processing video files.
"""
import os
import subprocess
import tempfile
from django.core.files.base import ContentFile
from PIL import Image
from io import BytesIO


def extract_video_thumbnail(video_file, seek_time=0):
    """
    Extract a frame from a video file as a thumbnail using FFmpeg.

    Args:
        video_file: Django UploadedFile or FileField instance
        seek_time: Time in seconds to extract the frame (default: 0 for first frame)

    Returns:
        ContentFile containing the JPEG thumbnail, or None if extraction fails
    """
    try:
        # Create temporary file for the video
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_video:
            # Write video content to temp file
            for chunk in video_file.chunks():
                temp_video.write(chunk)
            temp_video_path = temp_video.name

        # Reset file pointer after reading
        video_file.seek(0)

        # Create temporary file for the thumbnail
        temp_thumb_path = tempfile.mktemp(suffix='.jpg')

        # Extract frame using FFmpeg
        # -ss: seek to position
        # -i: input file
        # -vframes 1: extract only 1 frame
        # -q:v 2: quality (2 is high quality)
        # -vf scale: resize to max 1280 width while maintaining aspect ratio
        command = [
            'ffmpeg',
            '-ss', str(seek_time),
            '-i', temp_video_path,
            '-vframes', '1',
            '-q:v', '2',
            '-vf', 'scale=1280:-1',
            '-y',  # Overwrite output file
            temp_thumb_path
        ]

        # Run FFmpeg command
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30
        )

        # Clean up temp video file
        try:
            os.unlink(temp_video_path)
        except:
            pass

        # Check if thumbnail was created successfully
        if result.returncode == 0 and os.path.exists(temp_thumb_path):
            # Read the thumbnail
            with open(temp_thumb_path, 'rb') as f:
                thumbnail_data = f.read()

            # Clean up temp thumbnail file
            try:
                os.unlink(temp_thumb_path)
            except:
                pass

            # Optimize the image using Pillow
            try:
                img = Image.open(BytesIO(thumbnail_data))

                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'LA', 'P'):
                    rgb_img = Image.new('RGB', img.size, (0, 0, 0))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    rgb_img.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                    img = rgb_img

                # Save optimized version
                output = BytesIO()
                img.save(output, format='JPEG', quality=85, optimize=True)
                output.seek(0)

                return ContentFile(output.read())
            except Exception as e:
                # If Pillow optimization fails, return original
                return ContentFile(thumbnail_data)

        else:
            # FFmpeg failed
            return None

    except Exception as e:
        # Log the error (you can add proper logging here)
        print(f"Error extracting video thumbnail: {e}")
        return None
    finally:
        # Ensure temp files are cleaned up
        try:
            if 'temp_video_path' in locals():
                os.unlink(temp_video_path)
        except:
            pass
        try:
            if 'temp_thumb_path' in locals() and os.path.exists(temp_thumb_path):
                os.unlink(temp_thumb_path)
        except:
            pass


def generate_thumbnail_filename(video_filename):
    """
    Generate a thumbnail filename based on the video filename.

    Args:
        video_filename: Original video filename

    Returns:
        Thumbnail filename with .jpg extension
    """
    base_name = os.path.splitext(os.path.basename(video_filename))[0]
    return f"{base_name}_thumb.jpg"
