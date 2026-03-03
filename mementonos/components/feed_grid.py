import reflex as rx
from reflex.components.core.breakpoints import Breakpoints
from mementonos.state.feed import MediaItem, FeedState
from mementonos.utils.logger import get_logger

logger = get_logger(__name__)

def feed_grid() -> rx.Component:
    """Сетка с медиафайлами."""
    return rx.vstack(
        # Условный рендеринг: если нет ключа, показываем заглушку
        rx.cond(
            FeedState.master_key,
            rx.vstack(
                # Сетка с файлами
                rx.grid(
                    rx.foreach(
                        FeedState.media_items,
                        lambda item: rx.box(
                            rx.vstack(
                                # Изображение/видео
                                rx.box(
                                    rx.image(
                                        src=item.thumbnail_url,
                                        object_fit="contain",
                                        border_radius="lg",
                                        loading="lazy"
                                    ),
                                    display="flex",
                                    align_items="center",
                                    justify_content="center",
                                    position="relative",
                                    width="100%",
                                    height="180px",
                                    on_click=lambda: rx.redirect(f"/media/{item.id}")
                                ),
                                spacing="1",
                            ),
                            border_width="2px",
                            border_style="solid",
                            border_color=rx.cond(
                                item.mime_type.startswith("video/"),
                                "blue",
                                "gray"
                            ),
                            border_radius="lg",
                            overflow="hidden",
                            cursor="pointer",
                            bg="gray",
                            _hover={
                                "transform": "scale(1.02)",
                                "transition": "transform 0.2s ease-out",
                                "box_shadow": "0 10px 25px -5px rgba(0, 0, 0, 0.5)",
                            },
                            transition="all 0.2s ease-out"
                        ),
                    ),
                    columns=Breakpoints(
                        base="1",
                        sm="2",
                        md="3",
                        lg="4",
                        xl="5",
                    ),
                    spacing="4",
                    width="99%",
                    margin_top="6px",
                ),
                # Пагинация
                rx.cond(
                    FeedState.total_pages > 1,
                    rx.hstack(
                        rx.button(
                            "←",
                            on_click=FeedState.go_to_page(FeedState.current_page - 1),
                            is_disabled=FeedState.current_page <= 1,
                            color="white",
                            height="40px",
                            width="40px",
                            border_radius="full",
                        ),
                        rx.button(FeedState.current_page,
                                    height="40px",
                                    width="40px",),
                        rx.button(
                            "→",
                            on_click=FeedState.go_to_page(FeedState.current_page + 1),
                            is_disabled=FeedState.current_page >= FeedState.total_pages,
                            color="white",
                            height="40px",
                            width="40px",
                            border_radius="full",
                        ),
                        spacing="4",
                        justify="center",
                        width="100%",
                        padding_y="8",
                    ),
                ),
                width="100%",
                spacing="6",
            ),
            # Если нет ключа - показываем кнопку для открытия модалки
            rx.hstack(
                rx.box(
                    rx.icon("lock", size=20, color="gray.600"),
                    bg="gray.800",
                    padding="2",
                    border_radius="full",
                    mb="4",
                ),
                rx.text(
                    "Введите пароль для доступа к медиафайлам",
                    color="gray.400",
                    text_align="center",
                ),
            ),
        ),
        width="100%",
    )

def decryption_modal():
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Доступ к защищенному контенту", color="black", mb="7"),
            rx.spacer(),
            rx.dialog.description("Введите пароль для расшифровки медиа.", color="black", mb="6"),
            rx.box(height="15px"),
            rx.hstack(
                rx.input(
                    placeholder="Пароль",
                    type="password",
                    value=FeedState.upload_password,
                    on_change=FeedState.set_upload_password,
                    bg="gray.800",
                    color="black",
                    width="100%"
                ),
                rx.button(
                    "Расшифровать",
                    on_click=FeedState.submit_decryption_password,
                    is_disabled=FeedState.upload_password == ""
                ),
                mb="6",
            ),
            bg="gray.800",
            color="white",
            padding="6",
            border_radius="8px",
            width="100%",
            max_w="400px"
        ),
        open=FeedState.show_decryption_modal
    )