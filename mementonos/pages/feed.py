import reflex as rx
from mementonos.state.auth import AuthState

class FeedState(AuthState):
    
    def on_load(self):
        if not self.authenticated:
            return rx.redirect("/")
        
        return self.load_feed_data()
    
    def load_feed_data(self):
        return