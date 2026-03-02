import reflex as rx
from mementonos.api.endpoints import get_fastapi_app

fastapi_app = get_fastapi_app()

app = rx.App(
    theme=rx.theme(
        appearance="light",
        accent_color="violet",
        radius="large",
        scaling="110%",
        has_background=True,
    ),
    api_transformer=fastapi_app
)