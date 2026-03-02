import reflex as rx
from reflex import Base
from typing import List
from pathlib import Path
from datetime import datetime
import os

from mementonos.utils.security import hash_password, encrypt_data, decrypt_master_key
from mementonos.models import User, FileEncrypted
from mementonos.utils.security import decode_jwt

from mementonos.utils.logger import get_logger

logger = get_logger(__name__)

class FileItem(Base):
    name: str
    size: float
    extension: str
    uploaded_at: datetime

class UploadState(rx.State):
    show_upload_modal: bool = False
    files: List[rx.UploadFile] = []
    file_info: List[FileItem] = []
    is_uploading: bool = False
    upload_progress: int = 0
    to_common: bool = False

    upload_password: str = ""

    token: str = rx.Cookie(name="mementonos_token", path="/")

    def open_upload_modal(self):
        self.show_upload_modal = True
        self.files = []
        self.to_common = False

    def close_upload_modal(self):
        self.show_upload_modal = False
        self.files = []
        self.is_uploading = False
        self.upload_progress = 0

    def set_to_common(self):
        self.to_common = not self.to_common

    async def handle_upload(self, files: list[rx.UploadFile]):
        async with self:
            self.files = files
            self.file_info = [
                FileItem(
                    name=f.filename or "Без имени",
                    size=f.size or 0,
                    extension=Path(f.name or f.filename or "").suffix.lower() or "",
                    uploaded_at=datetime.utcnow()
                )
                for f in files
            ]

    @rx.event(background=True)
    async def start_upload(self):
        if not self.files:
            yield rx.toast.error("Выберите хотя бы один файл")
            return
        
        if not self.upload_password:
            yield rx.toast.error("Введите пароль")
            return
        
        token = self.token

        try:
            payload = decode_jwt(token)
            user_id = int(payload.get("sub"))
        except:
            yield rx.toast.error("Недействительный токен")
            return

        with rx.session() as session:
            user = session.get(User, user_id)
            pair_id = user.pair_id
            if hash_password(self.upload_password) != user.hashed_pw:
                yield rx.toast.error("Неверный пароль")
                return

        try:
            master_key = decrypt_master_key(user.encrypted_master_key, self.upload_password, user.kdf_salt)
        except Exception as e:
            logger.error(f"Ошибка доступа к ключу: {str(e)}")
            return
        async with self:
            self.is_uploading = True
            self.upload_progress = 0

        try:
            total = len(self.files)
            processed = 0

            base_dir = os.getenv("DATA_DIR") / Path("user_data") / str(pair_id)
            if self.to_common:
                upload_dir = base_dir / "common"
            else:
                upload_dir = base_dir / str(user_id)

            upload_dir.mkdir(parents=True, exist_ok=True)

            for file, file_info in zip(self.files, self.file_info):
                content = await file.read()
                encrypted_content = encrypt_data(content, master_key)
                encrypted_name = encrypt_data(file_info.name.encode("utf-8"), master_key).decode('utf-8')
                given_filename = f"{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{os.urandom(4).hex()}.enc"
                file_path = upload_dir / given_filename

                with open(file_path, "wb") as f:
                    f.write(encrypted_content)

                file_item = FileEncrypted(
                    file_path=str(file_path),
                    original_size=len(content),
                    encrypted_name=encrypted_name,
                    extension=file_info.extension,
                    uploaded_by_id=user_id,
                    is_common=self.to_common,
                )

                with rx.session() as session:
                    session.add(file_item)
                    session.commit()

                logger.info(f"Wrote {file_info.name}")

                processed += 1
                async with self:
                    self.upload_progress = int((processed / total) * 100)
                yield

            if self.upload_progress == 100:
                yield rx.toast.success(f"Загружено {total} файлов")
                async with self:
                    self.close_upload_modal()

        except Exception as e:
            yield rx.toast.error(f"Ошибка загрузки: {str(e)}")

        finally:
            async with self:
                self.is_uploading = False