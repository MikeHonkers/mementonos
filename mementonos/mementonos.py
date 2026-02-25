from dotenv import load_dotenv

load_dotenv()

import reflex as rx
from mementonos.pages import index, feed 

app = rx.App(
    theme=rx.theme(
        appearance="light",
        accent_color="violet",
        radius="large",
        scaling="110%",
        has_background=True,
    )
)