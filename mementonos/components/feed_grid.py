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
                                ),
                                spacing="1",
                            ),
                            border_width="1px",
                            border_style="solid",
                            border_color=rx.cond(
                                item.mime_type.startswith("video/"),
                                "blue.600",
                                "gray.700"
                            ),
                            border_radius="lg",
                            overflow="hidden",
                            cursor="pointer",
                            bg="gray.800",
                            _hover={
                                "transform": "scale(1.02)",
                                "transition": "transform 0.2s ease-out",
                                "box_shadow": "0 10px 25px -5px rgba(0, 0, 0, 0.5)",
                                "border_color": "blue.500",
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
                    width="100%",
                ),
                # Пагинация
                rx.cond(
                    FeedState.total_pages > 1,
                    rx.hstack(
                        rx.button(
                            "←",
                            on_click=FeedState.go_to_page(FeedState.current_page - 1),
                            is_disabled=FeedState.current_page <= 1,
                            bg="gray.700",
                            color="white",
                            _hover={"bg": "gray.600"},
                            _disabled={"bg": "gray.800", "opacity": 0.5},
                            height="40px",
                            width="40px",
                            border_radius="full",
                        ),
                        rx.hstack(
                            rx.foreach(
                                rx.Var.range(
                                    rx.cond(
                                        FeedState.total_pages > 5,
                                        5,
                                        FeedState.total_pages
                                    )
                                ),
                                lambda i: rx.button(
                                    i + 1,
                                    on_click=FeedState.go_to_page(i + 1),
                                    bg=rx.cond(
                                        FeedState.current_page == i + 1,
                                        "blue.600",
                                        "gray.700"
                                    ),
                                    color="white",
                                    _hover={"bg": "blue.700"},
                                    height="40px",
                                    width="40px",
                                    border_radius="full",
                                )
                            ),
                            spacing="2",
                        ),
                        rx.button(
                            "→",
                            on_click=FeedState.go_to_page(FeedState.current_page + 1),
                            is_disabled=FeedState.current_page >= FeedState.total_pages,
                            bg="gray.700",
                            color="white",
                            _hover={"bg": "gray.600"},
                            _disabled={"bg": "gray.800", "opacity": 0.5},
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
            rx.vstack(
                rx.box(
                    rx.icon("lock", size=40, color="gray.600"),
                    bg="gray.800",
                    padding="8",
                    border_radius="full",
                    mb="4",
                ),
                rx.heading(
                    "Контент зашифрован",
                    color="white",
                ),
                rx.text(
                    "Введите пароль для доступа к медиафайлам",
                    color="gray.400",
                    text_align="center",
                ),
                rx.button(
                    "Ввести пароль",
                    on_click=FeedState.open_decryption_modal,
                    bg="blue.600",
                    color="white",
                    mt="4",
                    _hover={"bg": "blue.700"},
                ),
                justify="center",
                align="center",
                height="50vh",
                width="100%",
                spacing="4",
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