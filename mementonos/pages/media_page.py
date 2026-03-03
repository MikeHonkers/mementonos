import reflex as rx
import os
from typing import Optional
from mementonos.state.feed import FeedState
from mementonos.state.auth import AuthState
from mementonos.models import FileEncrypted
from mementonos.state.feed import get_mime_type, MediaItem
from mementonos.utils.logger import get_logger
from mementonos.utils.cache import get_master_key
from mementonos.utils.security import decode_jwt, decrypt_data

logger = get_logger(__name__)

class MediaPageState(FeedState):
    selected_media: Optional[MediaItem] = None

    @rx.event
    def load_from_route(self):
        try:
            media_id = self.router.page.params["id"]
            self.load_media_by_id(media_id)
        except ValueError:
            return rx.text("Неверный ID медиафайла")

    def load_media_by_id(self, media_id: str):
        """Загрузка конкретного медиафайла по ID."""
        payload = decode_jwt(self.token)
        user_id = int(payload.get("sub"))
        self.master_key = get_master_key(user_id)
        
        if not self.master_key:
            return rx.redirect('/feed')
        
        with rx.session() as session:
            media_id = int(media_id)
            file = session.get(FileEncrypted, media_id)

            if not file:
                logger.error(f"Файл с ID {media_id} не найден")
                self.selected_media = None
                return

            original_name = decrypt_data(file.encrypted_name.encode('utf-8'), self.master_key).decode('utf-8')

            file_url = os.getenv("BACKEND_URL") + f"/api/media/{file.id}/file"
            thumbnail_url = os.getenv("BACKEND_URL") +  f"/api/media/{file.id}/thumbnail"
            mime_type = get_mime_type(file.extension)

            self.selected_media = MediaItem(
                id=file.id,
                thumbnail_url=thumbnail_url,
                file_url=file_url,
                original_name=original_name,
                upload_date=file.uploaded_at,
                file_size=file.original_size,
                mime_type=mime_type,
            )


def media_content() -> rx.Component:
    """Контент страницы медиа."""
    return rx.cond(
        FeedState.master_key,
        rx.vstack(
            # Изображение или видео
            rx.cond(
                MediaPageState.selected_media.mime_type.startswith("video/"),
                rx.box(
                    rx.video(
                        src=MediaPageState.selected_media.file_url,
                        width="100%",
                        height="100%",
                        controls=True,
                        object_fit="contain",
                    ),
                    width="480px",
                    height="270px",
                    overflow="hidden",
                ),
                rx.image(
                    src=MediaPageState.selected_media.file_url,
                    width="600",
                    height="100%",
                ),
            ),
            # Информация о файле
            rx.vstack(
                rx.heading(
                    MediaPageState.selected_media.original_name,
                    size="5",
                ),
                rx.text(f"Дата загрузки: {MediaPageState.selected_media.upload_date}"),
                rx.text(f"Размер: {MediaPageState.selected_media.file_size // 1024} KB"),
                rx.text(f"Тип: {MediaPageState.selected_media.mime_type}"),
                rx.cond(
                    MediaPageState.selected_media.width & MediaPageState.selected_media.height,
                    rx.text(f"Разрешение: {MediaPageState.selected_media.width}x{MediaPageState.selected_media.height}"),
                ),
                rx.cond(
                    MediaPageState.selected_media.duration,
                    rx.text(f"Длительность: {MediaPageState.selected_media.duration} сек"),
                ),
                spacing="3",
                align="start",
                width="100%",
                max_width="800px",
                padding="4",
                border_radius="lg",
                border="1px solid rgba(255,255,255,0.1)",
            ),
            spacing="6",
            width="100%",
            align="center",
        ),
        # Если нет ключа - показываем заглушку
        rx.vstack(
            rx.box(
                rx.icon("lock", size=40),
                bg="gray.800",
                padding="4",
                border_radius="full",
            ),
            rx.heading("Доступ запрещен", size="5"),
            rx.text("Введите пароль для доступа к медиафайлам"),
            rx.button(
                "Ввести пароль",
                on_click=FeedState.open_decryption_modal,
            ),
            spacing="4",
            width="100%",
            height="50vh",
            align="center",
            justify="center",
        ),
    )

def back_button() -> rx.Component:
    """Кнопка возврата к ленте."""
    return rx.hstack(
        rx.button(
            "← Назад к ленте",
            on_click=rx.redirect("/feed"),
            variant="soft",
            mb="4",
        ),
        width="100%",
        justify="start",
        mb="4",
    )

@rx.page(
    route="/media/[id]",
    title="Просмотр медиа",
    on_load=[
        AuthState.check_auth,
        AuthState.redirect_root_based_on_auth,
        MediaPageState.load_from_route,
    ]
)
def media_page() -> rx.Component:
    """Страница отдельного медиафайла."""
    
    return rx.fragment(
        rx.vstack(
            rx.box(
                back_button(),
                media_content(),
                width="100%",
                flex_grow="1",
                overflow_y="auto",
                padding="4",
            ),
            width="100%",
            height="100vh",
            spacing="0",
            direction="row",
        ),
        background="gray.900",
        color="white",
    )