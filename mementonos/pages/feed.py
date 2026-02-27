import reflex as rx
from mementonos.state.auth import AuthState
from mementonos.components.sidebar import sidebar
from mementonos.components.feed_grid import feed_grid

@rx.page(
    route="/feed",
    title="Лента",
    on_load=[
        AuthState.check_auth,
        AuthState.redirect_based_on_auth,
    ]
)
def feed():
    return rx.fragment(
        rx.vstack(
            sidebar(),
            rx.box(
                feed_grid(),
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