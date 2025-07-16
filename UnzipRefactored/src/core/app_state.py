
# src/core/app_state.py
class AppState:
    def __init__(self):
        self.product_name = None
        self.must_include = None
        self.conversion_targets = []
        self.conversion_targets_mapping = {}

global_state = AppState()
