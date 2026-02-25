import reflex as rx
from mementonos.state.auth import AuthState

def auth_page():
    """Главная страница с выбором: войти или создать пару"""
    return rx.center(
        rx.vstack(
            rx.heading(
                "MementoNos",
                size="9",
                color="var(--ctp-text)",
                mb="10",
                text_align="center",
            ),
            rx.text(
                "Ваши воспоминания — только для вас двоих",
                size="5",
                color="var(--ctp-subtext0)",
                mb="12",
                text_align="center",
            ),
            rx.hstack(
                rx.button(
                    "Войти",
                    size="4",
                    width="200px",
                    height="90px",
                    font_size="28px",
                    on_click=AuthState.open_login,
                    color_scheme="blue",
                ),
                rx.button(
                    "Создать пару",
                    size="4",
                    width="200px",
                    height="90px",
                    font_size="28px",
                    on_click=AuthState.open_create_pair,
                    color_scheme="violet",
                ),
                rx.button(
                    "Найти пару",
                    size="4",
                    width="200px",
                    height="90px",
                    font_size="28px",
                    on_click=AuthState.open_find_pair,
                    color_scheme="green",
                ),
                spacing="9",
                justify="center",
            ),
            spacing="8",
            align="center",
            width="100%",
            z_index="10",
            max_width="800px",
        ),
        height="100vh",
        width="100vw",
        background_size="cover",
        background_image="linear-gradient(to bottom right, #fdf2f8, #f9e4f0, #f5d5e8, #f0c6e0)",
        position="relative",
        _before={
            "content": '""',
            "position": "absolute",
            "inset": "0",
            "background": """
                radial-gradient(ellipse at 10% 85%, #d7aaff 0%, transparent 50%),
                radial-gradient(circle at 80% 20%, #ffccff 0%, transparent 45%),
                radial-gradient(ellipse at 40% 60%, #c89eff 0%, transparent 70%),
                radial-gradient(circle at 65% 75%, #e0bbff 0%, transparent 60%)
            """,
            "opacity": "0.7",
            "filter": "blur(35px)",
            "pointer_events": "none",
            "z_index": "-1",
        },
    )


def auth_modal():
    """Модалка, которая открывается при нажатии на кнопки"""
    return rx.dialog.root(
        rx.dialog.trigger(rx.text("")),  # скрытый триггер, открываем через состояние
        rx.dialog.content(
            rx.dialog.title(
                rx.cond(
                    AuthState.modal_type == "login", "Вход",
                    rx.cond(
                        AuthState.modal_type == "create_pair", "Создать пару",
                        "Найти пару"
                    )
                )
            ),
            rx.dialog.description(
                rx.vstack(
                    rx.input(
                        placeholder="Никнейм",
                        value=AuthState.username,
                        on_change=AuthState.set_username,
                        width="100%",
                    ),
                    rx.input(
                        placeholder="Пароль",
                        type="password",
                        value=AuthState.password,
                        on_change=AuthState.set_password,
                        width="100%",
                    ),
                    rx.cond(
                        AuthState.modal_type != "login",
                        rx.input(
                            placeholder="Повтори пароль",
                            type="password",
                            value=AuthState.password_confirm,
                            on_change=AuthState.set_password_confirm,
                            width="100%",
                        ),
                    ),
                    
                    rx.cond(
                        AuthState.modal_type == "find_pair",
                        rx.input(
                            placeholder="Код пары (6 символов)",
                            value=AuthState.pair_code_input,
                            on_change=AuthState.set_pair_code_input,
                            width="100%",
                        ),
                    ),
                    rx.cond(
                        AuthState.generated_code != "",
                        rx.vstack(
                            rx.text(
                                f"Код пары: {AuthState.generated_code}",
                                color="green",
                                weight="bold",
                                text_align="center",
                            ),
                            rx.text(
                                "Осталось: ",
                                rx.text(
                                    AuthState.time_left_str,
                                    as_="span",
                                    color="var(--ctp-text)",
                                ),
                                color="var(--ctp-subtext0)",
                                text_align="center",
                                size="3",
                            ),
                            align="center",
                            spacing="1",
                            mt="4",
                        ),
                    ),
                    
                    rx.text(AuthState.error_message, color="red", text_align="center", mt="2"),
                    spacing="4",
                    width="100%",
                    align_items="stretch",
                ),
                margin_bottom="1.5rem",
            ),
            rx.hstack(
                rx.dialog.close(
                    rx.button("Отмена", variant="soft", color_scheme="gray")
                ),
                rx.cond(
                    AuthState.modal_type == "login",
                    rx.button("Войти", on_click=AuthState.login, color_scheme="blue"),
                ),
                rx.cond(
                    AuthState.modal_type == "create_pair",
                    rx.button(
                        "Сгенерировать код",
                        on_click=AuthState.generate_pair_code,
                        color_scheme="violet",
                    ),
                ),
                rx.cond(
                    AuthState.modal_type == "find_pair",
                    rx.button(
                        "Присоединиться",
                        on_click=AuthState.join_pair,
                        color_scheme="green",
                    ),
                ),
                spacing="3",
                justify="end",
                width="100%",
            ),
            width="420px",
            padding="6",
            border_radius="lg",
        ),
        open=AuthState.show_modal,
        on_open_change=AuthState.set_show_modal,
    )