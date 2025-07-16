# src/gui/gui_main.py
import customtkinter as ctk
import datetime
import sys
from src.config.config import DEMO_MODE, LIMIT_DAYS, LAUNCH_CUTOFF_DATE, VERSION_INFO
import src.utils.logging_utils as logu
from src.utils.logging_utils import log_user, log_debug, log_box_widget
from src.utils.resource_utils import resource_path
from .gui_styles import get_styles
from .components.run_frame import RunFrame
from .components.manage_frame import ManageFrame

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.resizable(False, False)
        self.title("Unzip Helper")
        self.geometry("500x750")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.styles = get_styles()
        ico_path = resource_path("src/assets/unzip.ico")
        self.iconbitmap(ico_path)

        self.title_bar = ctk.CTkFrame(self, height=50, fg_color="#f0f0f0")
        self.title_bar.grid(row=0, column=0, sticky="ew")
        self.title_bar.grid_columnconfigure(0, weight=1)

        self.title_label = ctk.CTkLabel(
            self.title_bar,
            text="Unzip Helper",
            **self.styles["FONT_TITLE"]
        )
        self.title_label.grid(row=0, column=0, padx=20, pady=(12, 8), sticky="w")

        self.tabview = ctk.CTkTabview(self, fg_color="#f9f9f9")
        self.tabview.configure(height=520)
        self.tabview.grid(row=1, column=0, padx=20, pady=(5, 5), sticky="nsew")

        self.tabview.add("Run")
        self.tabview.add("Add/Delete Products")

        self.tab_exec = self.tabview.tab("Run")
        self.tab_conf = self.tabview.tab("Add/Delete Products")
        self.tab_exec.configure(fg_color="#f9f9f9")
        self.tab_conf.configure(fg_color="#f9f9f9")
        self.tab_exec.grid_rowconfigure(0, weight=1)
        self.tab_exec.grid_columnconfigure(0, weight=1)
        self.tab_conf.grid_rowconfigure(0, weight=1)
        self.tab_conf.grid_columnconfigure(0, weight=1)
        self.tabview.configure(command=self.on_tab_change)

        self.run_frame = RunFrame(self.tab_exec, self.styles)
        self.run_frame.grid(row=0, column=0, sticky="")

        self.manage_frame = ManageFrame(self.tab_conf, self.styles)
        self.manage_frame.grid(row=0, column=0, sticky="")

        self.footer_label = ctk.CTkLabel(self, text=f"Unzip Helper v{VERSION_INFO}", height=30, text_color="gray", font=self.styles["FONT_REGULAR"])
        self.footer_label.grid(row=2, column=0, pady=(0, 2), sticky="s")

        self.log_box = ctk.CTkTextbox(self, height=120, font=self.styles["FONT_REGULAR"])
        self.log_box.grid(row=3, column=0, padx=20, pady=(0, 10), sticky="ew")

        logu.init_logging()
        self.after(100, self.after_gui_loaded)

    def on_tab_change(self):
        current_tab = self.tabview.get()
        if current_tab == "Run":
            self.run_frame.reload_dropdown()
        elif current_tab == "Add/Delete Products":
            self.manage_frame.reload_dropdown()

    def after_gui_loaded(self):
        global log_box_widget
        sys.stdout = logu.InfoOnlyLogger(self.log_box)
        sys.stderr = logu.InfoOnlyLogger(self.log_box)
        log_user("Start Logging")
        log_debug("Debug also here!")
        print("[INFO] Manual info print")
        self.update_footer_label()
        self.run_frame.reload_dropdown()
        log_box_widget = self.log_box

    def update_footer_label(self):
        today = datetime.date.today()
        days_passed = (today - LAUNCH_CUTOFF_DATE).days
        remaining_days = LIMIT_DAYS - days_passed if DEMO_MODE else 999
        if remaining_days < 0:
            self.footer_label.configure(text=f"Unzip Helper v{VERSION_INFO}  •  Invalid system date")
        elif not DEMO_MODE:
            self.footer_label.configure(text=f"Unzip Helper v{VERSION_INFO}  •  Official Version")
        else:
            self.footer_label.configure(text=f"Unzip Helper v{VERSION_INFO}  •  {remaining_days} days remaining")

def main():
    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("green")
    app = App()
    app.mainloop()

if __name__ == "__main__":
    main()