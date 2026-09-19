import os
import subprocess
import tempfile
from django.core.files.base import ContentFile
from PIL import Image
from io import BytesIO

def extract_video_thumbnail(video_file, seek_time=0):
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_video:
            for chunk in video_file.chunks():
                temp_video.write(chunk)
            temp_video_path = temp_video.name
        video_file.seek(0)
        temp_thumb_path = tempfile.mktemp(suffix='.jpg')
        command = [
            'ffmpeg', '-ss', str(seek_time), '-i', temp_video_path,
            '-vframes', '1', '-q:v', '2', '-vf', 'scale=1280:-1',
            '-y', temp_thumb_path
        ]
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
        try:
            os.unlink(temp_video_path)
        except:
            pass
        if result.returncode == 0 and os.path.exists(temp_thumb_path):
            with open(temp_thumb_path, 'rb') as f:
                thumbnail_data = f.read()
            try:
                os.unlink(temp_thumb_path)
            except:
                pass
            try:
                img = Image.open(BytesIO(thumbnail_data))
                if img.mode in ('RGBA', 'LA', 'P'):
                    rgb_img = Image.new('RGB', img.size, (0, 0, 0))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    rgb_img.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                    img = rgb_img
                output = BytesIO()
                img.save(output, format='JPEG', quality=85, optimize=True)
                output.seek(0)
                return ContentFile(output.read())
            except Exception:
                return ContentFile(thumbnail_data)
        else:
            return None
    except Exception as e:
        print(f"Error extracting video thumbnail: {e}")
        return None
    finally:
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
    base_name = os.path.splitext(os.path.basename(video_filename))[0]
    return f"{base_name}_thumb.jpg"