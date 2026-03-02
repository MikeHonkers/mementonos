import reflex as rx
from mementonos.state.upload import UploadState

def upload_modal() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(
                rx.text("Загрузка медиа", font_size="xl", font_weight="bold"),
                background="purple.50",
                padding="6px", 
            ),
            rx.dialog.description(
                rx.vstack(
                    # Зона загрузки — основной контейнер rx.upload
                    rx.upload(
                        rx.vstack(
                            rx.icon("upload", size=48, color="gray.500"),
                            rx.text(
                                "Перетащите файлы сюда или кликните для выбора",
                                color="gray.600",
                                text_align="center",
                            ),
                            rx.text(
                                "Файлы до 1 ГБ",
                                font_size="sm",
                                color="gray.500",
                            ),
                            spacing="4",
                            align="center",
                            padding="8px",
                            width="100%",
                            background="gray.50",
                        ),
                        on_drop=UploadState.handle_upload,
                        multiple=True,
                        max_files=20,
                        max_size=1024 * 1024 * 1024,  # 1 ГБ
                        width="100%",
                    ),

                    rx.cond(
                        UploadState.files.length() > 0,
                        rx.box(
                            rx.text(
                                f"Выбрано файлов: {UploadState.files.length()}",
                                font_weight="medium",
                                margin_bottom="2px",
                            ),
                            rx.foreach(
                                UploadState.file_info,
                                lambda item: rx.hstack(
                                    rx.text(
                                        item["name"],
                                        no_wrap=True,
                                        overflow="hidden",
                                        text_overflow="ellipsis",
                                        flex="1",
                                    ),
                                    rx.spacer(),
                                    rx.text(
                                        f"{item["size"] / (1024*1024):.2f} МБ",
                                        color="gray.600",
                                        font_size="sm",
                                    ),
                                    width="100%",
                                    padding_y="5px",
                                    align_items="center",
                                )
                            ),
                            width="100%",
                            max_height="200px",
                            overflow_y="auto",
                            padding="4px",
                            border="1px solid #E2E8F0",
                            border_radius="md",
                            background="white",
                        ),
                    ),

                    rx.hstack(
                        rx.checkbox(
                            is_checked=UploadState.to_common,
                            on_change=UploadState.set_to_common,
                        ),
                        rx.text("Загрузить в общее хранилище"),
                        spacing="2",
                        align="center",
                        margin_top="4",
                    ),

                    rx.vstack(
                        rx.text("Введите пароль для шифрования", font_size="sm", color="gray.700", margin_bottom="1px"),
                        rx.input(
                            placeholder="Пароль...",
                            type="password",
                            value=UploadState.upload_password,
                            on_change=UploadState.set_upload_password,
                            width="100%",
                            padding="3px",
                            border_radius="md",
                            border="1px solid #CBD5E0",
                        ),
                        width="100%",
                        spacing="2",
                        margin_top="6px",
                    ),

                    spacing="6",
                    width="100%",
                ),
                padding="6px",
            ),

            rx.cond(
                UploadState.is_uploading,
                rx.vstack(
                    rx.progress(
                        value=UploadState.upload_progress,
                        is_indeterminate=UploadState.upload_progress <= 0,
                        color_scheme="purple",
                        height="8px",
                        width="100%",
                        margin_top="12px",
                        margin_bottom="8px",
                    ),
                    width="100%",
                    spacing="1",
                    padding_x="4px",
                    padding_bottom="2px",
                    visible=UploadState.is_uploading,
                ),
                rx.fragment(),
            ),

            rx.hstack(
                rx.dialog.close(
                    rx.button("Отмена", variant="outline", color_scheme="gray", on_click=UploadState.close_upload_modal),
                ),
                rx.button(
                    rx.cond(
                        UploadState.is_uploading,
                        rx.hstack(
                            rx.spinner(size="2"),
                            rx.text("Загрузка..."),
                            spacing="2",
                        ),
                        rx.text("Загрузить"),
                    ),
                    color_scheme="purple",
                    on_click=UploadState.start_upload,
                    is_loading=UploadState.is_uploading,
                    loading_text="Загрузка...",
                    is_disabled=UploadState.files.length() == 0 | UploadState.is_uploading,
                ),
                spacing="3",
                margin_top="6px",
                justify="end",
                width="100%",
                padding="12px"
            ),
            width="lg",
            max_width="600px",
            padding="0",
        ),
        open=UploadState.show_upload_modal
    )