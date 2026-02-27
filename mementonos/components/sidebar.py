import reflex as rx

def circular_progress(
    value: float | rx.Var[float],
    size: int | rx.Var[int] = 120,
    thickness: int | rx.Var[int] = 12,
    color: str = "#805AD5",
    track_color: str = "#E2E8F0",
    show_label: bool = True,
) -> rx.Component:

    center = int(size / 2)
    radius = int((size - thickness) / 2)
    circumference = 2 * 3.141592653589793 * radius
    offset = circumference * (1 - value / 100)

    view_box_str = f"0 0 {size} {size}"
    transform_str = f"rotate(-90 {center} {center})"

    track_circle = rx.el.circle(
        cx=center,
        cy=center,
        r=radius,
        fill="none",
        stroke=track_color,
        stroke_width=thickness,
    )

    progress_circle = rx.el.circle(
        cx=center,
        cy=center,
        r=radius,
        fill="none",
        stroke=color,
        stroke_width=thickness,
        stroke_dasharray=circumference,
        stroke_dashoffset=offset,
        transform=transform_str,
        transition="stroke-dashoffset 0.35s ease",
        stroke_linecap="round",
    )

    label_text = rx.el.text(
        f"{value}%",
        x="50%",
        y="50%",
        dominant_baseline="central",
        text_anchor="middle",
        font_size="1.5rem",
        font_weight="bold",
        fill="#2D3748", 
        user_select="none",
    )

    return rx.center(
        rx.box(
            rx.el.svg(
                [
                    track_circle,
                    progress_circle,
                    rx.cond(show_label, label_text),
                ],
                width=size,
                height=size,
                view_box=view_box_str,
            ),
            width=size,
            height=size,
        )
    )

def sidebar() -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.heading("Меню", size="5", margin_bottom="3", color="#2D3748", padding="12px"), 
            
            rx.vstack(
                rx.link(
                    rx.box(
                        rx.hstack(
                            rx.icon("image", size=20, color="#8D00A0"),
                            rx.text("Лента фото/видео", weight="medium", color="#2D3748"),
                            spacing="3",
                            align="center",
                            width="100%",
                        ),
                        padding="12px",
                        border_radius="8px",
                        width="100%",
                    ),
                    href="/feed",
                    width="100%",
                    underline="none",
                    _hover={"background_color": "#FFFFFF", "box_shadow": "sm"},
                ),
                rx.link(
                    rx.box(
                        rx.hstack(
                            rx.icon("calendar_1", size=20, color="#8D00A0"),
                            rx.text("Календарь событий", weight="medium", color="#2D3748"),
                            spacing="3",
                            align="center",
                            width="100%",
                        ),
                        padding="12px",
                        border_radius="8px",
                        width="100%",
                    ),
                    href="/calendar",
                    width="100%",
                    underline="none",
                    _hover={"background_color": "#FFFFFF", "box_shadow": "sm"},
                ),
                rx.link(
                    rx.box(
                        rx.hstack(
                            rx.icon("folder", size=20, color="#8D00A0"),
                            rx.text("Альбомы + несортированное", weight="medium", color="#2D3748"),
                            spacing="3",
                            align="center",
                            width="100%",
                        ),
                        padding="12px",
                        border_radius="8px",
                        width="100%",
                    ),
                    href="/albums",
                    width="100%",
                    underline="none",
                    _hover={"background_color": "#FFFFFF", "box_shadow": "sm"},
                ),
                rx.link(
                    rx.box(
                        rx.hstack(
                            rx.icon("upload", size=20, color="#8D00A0"),
                            rx.text("Загрузить медиа", weight="medium", color="#2D3748"),
                            spacing="3",
                            align="center",
                            width="100%",
                        ),
                        padding="12px",
                        border_radius="8px",
                        width="100%",
                    ),
                    href="/upload",
                    width="100%",
                    underline="none",
                    _hover={"background_color": "#FFFFFF", "box_shadow": "sm"},
                ),
                spacing="3",
                width="100%",
                margin_bottom="8",
            ),
            
            rx.heading("Статистика", size="5", margin_bottom="3", color="#2D3748", padding="12px"),
            
            rx.box(
                rx.vstack(
                    rx.hstack(
                        rx.text("Всего фотографий", color="#718096"),
                        rx.spacer(),
                        rx.text("0", weight="bold", color="#2D3748"),
                        width="100%"
                    ),
                    rx.hstack(
                        rx.text("Всего видео", color="#718096"),
                        rx.spacer(),
                        rx.text("0", weight="bold", color="#2D3748"),
                        width="100%"
                    ),
                    rx.hstack(
                        rx.text("Всего событий", color="#718096"),
                        rx.spacer(),
                        rx.text("0", weight="bold", color="#2D3748"),
                        width="100%"
                    ),
                    spacing="3",
                ),
                background="white",
                border_radius="8px",
                box_shadow="sm",
                width="90%",
                margin_left="12px",
                margin_right="auto",
            ),
            
            rx.vstack(
                rx.heading("Disk Usage", size="4", margin_bottom="3", color="#2D3748"),
                rx.center(
                    circular_progress(
                        value=0,
                        size=100,
                        thickness=10,
                        show_label=True,
                    ),
                    rx.text(
                        "0 / 1000 МБ",
                        font_size="sm",
                        color="#3C4757",
                        margin_top="3",
                    ),
                    direction="column",
                ),
                width="100%",
                align="center",
                margin_y="8",
            ),
            
            rx.heading("Режим ленты", size="5", margin_bottom="3", color="#2D3748", padding="12px"),
            rx.hstack(
                rx.button(
                    "НАШЕ",
                    variant="solid",
                    color_scheme="purple",
                    flex="1",
                    padding_y="3",
                ),
                rx.button(
                    "МОЁ",
                    variant="outline",
                    color_scheme="purple",
                    flex="1",
                    padding_y="3",
                ),
                spacing="3",
                margin_left="12px",
                width="90%",
            ),
            
            rx.spacer(),
            
            spacing="3",
            width="250px",
            padding="8",
            background="#AEDCF7",
            height="100vh",
            position="sticky",
            top="0",
            overflow_y="auto",
            border_right="1px solid #E2E8F0",
        ),
        width="270px",
        flex_shrink="0",
    )