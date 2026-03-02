import reflex as rx
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import Response
from mementonos.models import FileEncrypted
from mementonos.state.feed import get_mime_type
from mementonos.utils.security import decrypt_data, decode_jwt
from mementonos.utils.thumbnails import create_image_thumbnail, create_video_thumbnail, create_placeholder_thumbnail
from mementonos.utils.cache import get_master_key
import logging

logger = logging.getLogger(__name__)

def get_fastapi_app():

    fastapi_app = FastAPI(title="Mementonos API")

    @fastapi_app.get("/api/media/{item_id}/file")
    async def get_media_file(item_id: int, request: Request):
        """Отдаёт расшифрованный файл по ID."""
        token = request.cookies.get("mementonos_token")
        
        if not token:
            raise HTTPException(status_code=401, detail="Не авторизован")
        
        try:
            payload = decode_jwt(token)
            user_id = int(payload.get("sub"))
        except Exception:
            raise HTTPException(status_code=401, detail="Недействительный токен")
        
        with rx.session() as session:
            file_record = session.get(FileEncrypted, item_id)
            if not file_record:
                raise HTTPException(status_code=404, detail="Файл не найден")
            
            if file_record.uploaded_by_id != user_id:
                raise HTTPException(status_code=403, detail="Нет доступа к файлу")
        
        master_key = get_master_key(user_id)
        if not master_key:
            raise HTTPException(status_code=401, detail="Требуется мастер ключ")
        
        try:
            with open(file_record.file_path, 'rb') as f:
                encrypted_data = f.read()
            
            decrypted_data = decrypt_data(encrypted_data, master_key)
            
            mime_type, _ = get_mime_type(file_record.extension)
            
            return Response(
                content=decrypted_data,
                media_type=mime_type,
                headers={
                    "Content-Disposition": f'inline; filename="{decrypt_data(file_record.encrypted_name.encode("utf-8"), master_key).decode("utf-8")}"'
                }
            )
        except Exception as e:
            logger.error(f"Ошибка при расшифровке файла {item_id}: {e}")
            raise HTTPException(status_code=500, detail="Ошибка при чтении файла")

    @fastapi_app.get("/api/media/{item_id}/thumbnail")
    async def get_thumbnail(item_id: int, request: Request):
        token = request.cookies.get("mementonos_token")

        if not token:
            raise HTTPException(status_code=401, detail="Не авторизован")
        
        try:
            payload = decode_jwt(token)
            user_id = int(payload.get("sub"))
        except Exception:
            raise HTTPException(status_code=401, detail="Недействительный токен")
        
        with rx.session() as session:
            file_record = session.get(FileEncrypted, item_id)
            if not file_record:
                raise HTTPException(status_code=404, detail="Файл не найден")
            
            if file_record.uploaded_by_id != user_id:
                raise HTTPException(status_code=403, detail="Нет доступа к файлу")
        
        master_key = get_master_key(user_id)
        if not master_key:
            raise HTTPException(status_code=401, detail="Требуется мастер ключ")
        
        try:
            with open(file_record.file_path, 'rb') as f:
                encrypted_data = f.read()
            
            decrypted_data = decrypt_data(encrypted_data, master_key)
            
            if file_record.extension.lower() in ('.jpg', '.jpeg', '.png', '.gif', '.webp'):
                thumbnail_data = create_image_thumbnail(decrypted_data)
            elif file_record.extension.lower() in ('.mp4', '.mov', '.avi', '.mkv'):
                thumbnail_data = create_video_thumbnail(decrypted_data, file_record.extension)
            else:
                thumbnail_data = create_placeholder_thumbnail()
            
            return Response(
                content=thumbnail_data,
                media_type="image/jpeg",
                headers={"Cache-Control": "public, max-age=3600"}
            )
        except Exception as e:
            logger.error(f"Ошибка при создании миниатюры для {item_id}: {e}")
            raise HTTPException(status_code=500, detail="Ошибка при создании миниатюры")

    @fastapi_app.get("/api/health")
    async def health_check():
        return {"status": "ok"}

    logger.debug('registered FastAPI endpoints')

    return fastapi_app