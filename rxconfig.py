import reflex as rx

config = rx.Config(
    app_name="mementonos",
    db_url="sqlite:///mementonos.db",
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.TailwindV4Plugin(),
    ],
    pages={
        "index": "mementonos.pages.index:index",
        "feed": "mementonos.pages.feed:feed",
    }
)

