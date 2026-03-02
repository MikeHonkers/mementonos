import reflex as rx
from sqlmodel import select, func
import mimetypes
from mementonos.utils.security import decode_jwt, decrypt_master_key, hash_password, decrypt_data
from mementonos.utils.logger import get_logger
from mementonos.utils.cache import save_master_key
from mementonos.models import User, FileEncrypted
from typing import List, Optional
from datetime import datetime
from dotenv import load_dotenv
import os

load_dotenv()

logger = get_logger(__name__)

def get_mime_type(extension: str) -> str:
        """
        Определяет MIME-тип по расширению файла.
        Возвращает application/octet-stream для неизвестных типов.
        """
        mime_type, _ = mimetypes.guess_type(f"file{extension}")
        
        if mime_type:
            return mime_type
        
        custom_mimes = {
            '.webp': 'image/webp',
            '.mkv': 'video/x-matroska',
            '.mov': 'video/quicktime',
            '.avi': 'video/x-msvideo',
        }
        
        return custom_mimes.get(extension.lower(), 'application/octet-stream')

class MediaItem(rx.Base):
    """Модель расшифрованного медиафайла для отображения в ленте."""
    id: int
    thumbnail_url: str
    file_url: str
    original_name: str
    upload_date: datetime
    file_size: int
    mime_type: str
    width: Optional[int] = None
    height: Optional[int] = None
    duration: Optional[float] = None

class FeedState(rx.State):
    show_decryption_modal: bool = False
    upload_password: str = ""
    master_key: Optional[bytes] = None
    
    token: str = rx.Cookie(name="mementonos_token", path="/")

    media_items: List[MediaItem] = []
    current_page: int = 1
    total_pages: int = 1
    items_per_page: int = 40

    def open_decryption_modal(self):
        self.show_decryption_modal = True

    def close_decryption_modal(self):
        self.show_decryption_modal = False
        self.upload_password = ""

    def check_master_key(self):
        if self.master_key:
            return
        self.open_decryption_modal()

    def submit_decryption_password(self):
        """Сохранить пароль и закрыть окно."""
        if self.upload_password == "":
            yield rx.toast.error("Введите пароль.")
            return
        try:
            payload = decode_jwt(self.token)
            user_id = int(payload.get("sub"))
            with rx.session() as session:
                user = session.get(User, user_id)
                if hash_password(self.upload_password) != user.hashed_pw:
                    yield rx.toast.error("Неверный пароль")
                    return
                self.master_key = decrypt_master_key(user.encrypted_master_key, self.upload_password, user.kdf_salt)
                save_master_key(user_id, self.master_key)
                self.close_decryption_modal()

        except Exception as e:
            logger.error(f"Ошибка доступа к ключу: {str(e)}")
            yield rx.toast.error(f"Ошибка доступа к ключу: {str(e)}")
            return
        
    def load_media(self, page: int = 1):
        """Загрузить файлы текущего пользователя с пагинацией."""
        payload = decode_jwt(self.token)
        user_id = int(payload.get("sub"))
        self.media_items = []

        allowed_extensions = [
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp',
            '.mp4', '.mov', '.avi', '.mkv', '.webm'
        ]
        
        with rx.session() as session:
            # Базовый запрос: файлы, загруженные текущим пользователем
            base_query = select(FileEncrypted).where(
                FileEncrypted.uploaded_by_id == user_id,
                FileEncrypted.extension.in_(allowed_extensions)
            ).order_by(FileEncrypted.uploaded_at.desc())

            # Общее количество записей
            total_count = session.exec(
                select(func.count()).select_from(base_query.subquery())
            ).one()
            self.total_pages = (total_count + self.items_per_page - 1) // self.items_per_page

            # Пагинация
            offset = (page - 1) * self.items_per_page
            query = base_query.offset(offset).limit(self.items_per_page)
            items = session.exec(query).all()

        self.current_page = page
        for item in items:
            original_name = decrypt_data(item.encrypted_name.encode('utf-8'), self.master_key).decode('utf-8')

            file_url = os.getenv("BACKEND_URL") + f"/api/media/{item.id}/file"
            thumbnail_url = os.getenv("BACKEND_URL") +  f"/api/media/{item.id}/thumbnail"
            mime_type = get_mime_type(item.extension)

            media_item = MediaItem(
                id=item.id,
                thumbnail_url=thumbnail_url,
                file_url=file_url,
                original_name=original_name,
                upload_date=item.uploaded_at,
                file_size=item.original_size,
                mime_type=mime_type,
            )
            logger.debug(f"Appended with {media_item}")
            self.media_items.append(media_item)
        logger.info(f"loaded {len(items)} media files to media_items.")
        
    def on_load(self):
        if not self.master_key:
            self.open_decryption_modal()
        else:
            return FeedState.load_media(page=1)
        
    def go_to_page(self, page: int):
        """Перейти на указанную страницу."""
        if 1 <= page <= self.total_pages:
            return FeedState.load_media(page=page)