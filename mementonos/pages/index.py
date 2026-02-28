import reflex as rx
from mementonos.state.auth import AuthState
from mementonos.components.auth_form import auth_page, auth_modal

@rx.page(
    route="/",
    title="MementoNos",
    on_load=[AuthState.check_auth, AuthState.redirect_feed_based_on_auth]
)
def index():
    return rx.fragment(
        rx.cond(
            AuthState.authenticated,
            rx.center(
                rx.spinner(),
                rx.text("Перенаправляем в ленту..."),
                height="100vh",
            ),
            rx.fragment(
                auth_page(),
                auth_modal(),
            ),
        )
    )