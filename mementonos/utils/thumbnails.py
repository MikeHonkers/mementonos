from PIL import Image
import io
import tempfile
import subprocess
import os

from mementonos.utils.security import get_logger

logger = get_logger(__name__)

def create_image_thumbnail(image_data: bytes, size=(180, 180)) -> bytes:
    """Создаёт миниатюру из изображения."""
    with Image.open(io.BytesIO(image_data)) as img:
        img.thumbnail(size, Image.Resampling.LANCZOS)
        # Конвертируем в RGB для JPEG
        if img.mode in ('RGBA', 'LA', 'P'):
            rgb_img = Image.new('RGB', img.size, (255, 255, 255))
            rgb_img.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = rgb_img
        
        output = io.BytesIO()
        img.save(output, format='JPEG', quality=85)
        return output.getvalue()
    
def create_video_thumbnail(video_data: bytes, extension: str, size=(180, 180)) -> bytes:
    """Извлекает первый кадр видео."""
    with tempfile.NamedTemporaryFile(suffix=extension, delete=False) as tmp_video:
        tmp_video.write(video_data)
        tmp_video_path = tmp_video.name
    
    try:
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_thumb:
            tmp_thumb_path = tmp_thumb.name
        
        cmd = [
            'ffmpeg', '-i', tmp_video_path,
            '-ss', '00:00:01',
            '-vframes', '1',
            '-vf', f'scale={size[0]}:{size[1]}:force_original_aspect_ratio=decrease,pad={size[0]}:{size[1]}:(ow-iw)/2:(oh-ih)/2',
            '-y', tmp_thumb_path
        ]
        result = subprocess.run(cmd, capture_output=True)
        
        if result.returncode != 0:
            logger.error(f"FFmpeg error: {result.stderr.decode()}")
            return create_placeholder_thumbnail()
        
        with open(tmp_thumb_path, 'rb') as f:
            thumbnail_data = f.read()
        
        return thumbnail_data
    
    except Exception as e:
        logger.error(f"Ошибка создания миниатюры видео: {e}")
        return create_placeholder_thumbnail()
    
    finally:
        try:
            if tmp_video_path:
                os.unlink(tmp_video_path)
            if tmp_thumb_path:
                os.unlink(tmp_thumb_path)
        except:
            pass

def create_placeholder_thumbnail() -> bytes:
    """Создаёт заглушку."""
    img = Image.new('RGB', (180, 180), color=(73, 109, 137))
    output = io.BytesIO()
    img.save(output, format='JPEG')
    return output.getvalue()