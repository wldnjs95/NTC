# state.py
class AppState:
    def __init__(self):
        self.product_name = ""
        self.must_include = ""
        self.conversion_targets = []
        self.jpeg_quality = 100

global_state = AppState()