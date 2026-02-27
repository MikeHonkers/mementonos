import reflex as rx
from reflex.components.core.breakpoints import Breakpoints
from mementonos.state.feed import MediaItem

mock_items = [
    {
        "id": "0",
        "type": "photo",
        "url": r"D:\mementonos\assets\favicon.ico",
        "thumbnail": r"D:\mementonos\assets\favicon.ico",
    }
]

def feed_grid() -> rx.Component:
    return rx.grid(
        rx.foreach(
            # AppState.media_items,
            mock_items,
            lambda item: rx.box(
                rx.stack(
                    rx.image(
                        src=item.thumbnail,
                        width="100%",
                        height="180px",
                        object_fit="cover",
                        border_radius="md",
                        loading="lazy",
                    ),
                    rx.cond(
                        item.type == "video",
                        rx.box(
                            rx.icon("play", color="white", size=24),
                            position="absolute",
                            bottom="8px",
                            right="8px",
                            background="rgba(0, 0, 0, 0.6)",
                            padding="4px 8px",
                            border_radius="full",
                        )
                    ),
                ),
                border_width="3px",
                border_style="solid",
                border_color=rx.cond(
                    item.type == "video",
                    "blue.600",
                    "transparent"
                ),
                border_radius="md",
                overflow="hidden",
                cursor="pointer",
                position="relative",
                _hover={
                    "transform": "scale(1.03)",
                    "transition": "transform 0.15s ease-out",
                    "& img": {"filter": "brightness(0.9)"},
                },
                # on_click=lambda: AppState.set_selected_item(item),
            )
        ),
        columns=Breakpoints(
            base="2",
            sm="3",
            md="4",
            lg="5",
            xl="6",
        ),
        spacing="4",
        width="100%",
    )