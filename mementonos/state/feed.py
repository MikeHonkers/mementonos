import reflex as rx

class MediaItem(rx.Base):
    id: str
    type: str
    url: str
    thumbnail: str