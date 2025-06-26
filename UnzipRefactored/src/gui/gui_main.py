
import customtkinter as ctk
import platform
import datetime
import sys
import os
import tkinter.messagebox as msg

from src.config.config import DEMO_MODE, LIMIT_DAYS, LAUNCH_CUTOFF_DATE, VERSION_INFO
import src.utils.logging_utils as logu
from src.utils.logging_utils import log_user, log_debug, log_error
from src.utils.general_utils import get_files_with_ext
from src.utils.zip_utils import unzip_selected_files
from src.utils.image_utils import convert_images_to_jpg
from src.utils.state import global_state
from src.utils.resource_utils import resource_path
from src.utils.product_store import load_products, update_recent_product, delete_product, save_products
from .gui_styles import get_styles


class SubFrame1(ctk.CTkFrame):
    def __init__(self, parent, styles):
        super().__init__(parent)
        self.styles = styles
        self.grid_columnconfigure((0, 2), weight=1)
        self.grid_columnconfigure(1, weight=0)
        self.configure(fg_color="#f9f9f9")

        self.current_products = load_products()
        self.recent_product = self.current_products.get('recent_product', None)
        self.product_dict = self.current_products.get('product_list', {})
        self.must_include_map = {}
        
        self.label_dropdown = ctk.CTkLabel(self, text="상품명", **self.styles["LABEL_STYLE"])
        self.label_dropdown.grid(row=0, column=1, pady=(20, 0), sticky="w")


        self.placeholder = "<-- Select -->"
        self.dropdown_values = [self.placeholder]
        for eng, info in self.product_dict.items():
            kor = info.get("must_include", "")
            self.dropdown_values.append(kor)
            self.must_include_map[kor] = eng
        
        self.dropdown = ctk.CTkOptionMenu(self, values=self.dropdown_values, width=220, **self.styles["OPTION_MENU_STYLE"])
        self.dropdown.grid(row=1, column=1, pady=(5, 40))
        self.dropdown.set(self.placeholder)

        self.run_button = ctk.CTkButton(self, text="실행", command=self.run_script, width=220, **self.styles["BUTTON_PRIMARY_STYLE"])
        self.run_button.grid(row=2, column=1, pady=(0, 10))

        self.status_label = ctk.CTkLabel(self, text="", text_color="gray")
        self.status_label.grid(row=3, column=1, pady=(0, 10), sticky="w")

        if self.recent_product:
            kor = self.product_dict.get(self.recent_product, {}).get("must_include", "")
            if kor in self.dropdown_values:
                self.dropdown.set(kor)

    def run_script(self):
        # ─── Demo Mode Check ───
        if DEMO_MODE:
            print("[DEBUG] DEMO_MODE:", DEMO_MODE)
            print("[DEBUG] LIMIT_DAYS:", LIMIT_DAYS)
            print("[DEBUG] LAUNCH_CUTOFF_DATE:", LAUNCH_CUTOFF_DATE)
            today = datetime.date.today()
            days_passed = (today - LAUNCH_CUTOFF_DATE).days
            if days_passed > LIMIT_DAYS:
                msg.showerror("Demo Expired", "New version required.")
                log.debug(f"[DEBUG] Demo expired. Days passed: {days_passed}, Limit: {LIMIT_DAYS}")
                self.status_label.configure(text="⛔ Demo Expired.", text_color="red")
                return
        
        global_state.conversion_targets = []
            
        selected_korean = self.dropdown.get()
        if selected_korean == self.placeholder:
            msg.showwarning("Selection Error", "Please select a product.")
            return

        update_recent_product(selected_korean)
        product_name = self.must_include_map.get(selected_korean)
        product_info = self.product_dict.get(product_name)
        keyword = product_info["must_include"]

        global_state.product_name = product_name
        global_state.must_include = keyword

        aep_count = get_files_with_ext(os.getcwd(), '.aep')
        if len(aep_count) > 1:
            self.status_label.configure(text="Error: Multiple AEP files found.", text_color="red")
            return
        elif len(aep_count) == 0:
            log_debug(f"No AEP file found in the current directory. Expected: {os.getcwd()}")
            self.status_label.configure(text="Error: AEP file not found", text_color="red")
            return

        self.status_label.configure(text="Running...", text_color="lightblue")

        try:
            global_state.conversion_targets = []
            unzip_selected_files(os.getcwd())
            for path in global_state.conversion_targets:
                if not os.path.exists(path):
                    log_error(f"[CRITICAL] Target directory does NOT exist: {path}")
                    raise FileNotFoundError(f"Target directory does NOT exist: {path}")
                else:
                    converted, errors = convert_images_to_jpg(path)
                if errors > 0:
                    log_error(f"Conversion errors occurred in {path}.")
                    self.status_label.configure(text=f"⚠️ Conversion Errors: {errors}", text_color="red")
                    return
            self.status_label.configure(text="Completed Successfully.", text_color="green")
            log_user(f"Execution Completed: {product_name}")
            
        except Exception as e:
            log_error(str(e))
            self.status_label.configure(text="⚠️ Error Occurred. Check Log", text_color="red")

    def reload_dropdown(self):
        self.current_products = load_products()
        self.product_dict = self.current_products.get("product_list", {})
        self.must_include_map = {}
        self.dropdown_values = [self.placeholder]
        for eng, info in self.product_dict.items():
            kor = info.get("must_include", "")
            self.dropdown_values.append(kor)
            self.must_include_map[kor] = eng
        self.dropdown.configure(values=self.dropdown_values)

        # Recent value handling
        recent_kor = self.current_products.get("recent_product")
        if recent_kor in self.dropdown_values:
            self.dropdown.set(recent_kor)
        else:
            self.dropdown.set(self.placeholder)


class SubFrame2(ctk.CTkFrame):
    def __init__(self, parent, styles):
        super().__init__(parent)
        self.styles = styles
        self.grid_columnconfigure((0, 2), weight=1)
        self.grid_columnconfigure(1, weight=0)
        self.configure(fg_color="#f9f9f9")

        self.inner = ctk.CTkFrame(self, fg_color="#f9f9f9")
        self.inner.grid(row=0, column=1, pady=(10, 10), sticky="n")
        self.inner.grid_columnconfigure(0, weight=1)
        
        self.label_add = ctk.CTkLabel(self.inner, text="상품 추가", **self.styles["LABEL_STYLE"])
        self.label_add.grid(row=0, column=0, pady=(20, 6), sticky="w")

        self.entry_product = ctk.CTkEntry(self.inner, placeholder_text="상품명 (예: popcorn)", width=240, **self.styles["ENTRY_STYLE"])
        self.entry_product.grid(row=1, column=0, pady=(0, 0), sticky="ew")
        
        self.entry_product_description = ctk.CTkLabel(self.inner, text="상품명은 영문자만 사용하세요.", **self.styles["DESCRIPTION_STYLE"])
        self.entry_product_description.grid(row=2, column=0, pady=(0, 10), sticky="nw")

        self.entry_keyword = ctk.CTkEntry(self.inner, placeholder_text="키워드 (예: 팝콘)", width=240, **self.styles["ENTRY_STYLE"])
        self.entry_keyword.grid(row=3, column=0, pady=(0, 0), sticky="ew")

        self.entry_keyword_description = ctk.CTkLabel(self.inner, text="키워드는 한글로 입력하세요.", **self.styles["DESCRIPTION_STYLE"])
        self.entry_keyword_description.grid(row=4, column=0, pady=(0, 10), sticky="nw")

        self.add_button = ctk.CTkButton(self.inner, text="추가", width=240, command=self.add_product, **self.styles["BUTTON_PRIMARY_STYLE"])
        self.add_button.grid(row=5, column=0, pady=(0, 20), sticky="ew")
        
        separator = ctk.CTkFrame(self.inner, height=1, fg_color="#979797")
        separator.grid(row=6, column=0, sticky="ew", pady=15)

        self.label_delete = ctk.CTkLabel(self.inner, text="상품 삭제", **self.styles["LABEL_STYLE"])
        self.label_delete.grid(row=7, column=0, pady=(0, 6), sticky="w")

        self.dropdown = ctk.CTkOptionMenu(self.inner, values=["<-- Select -->"], width=240, **self.styles["OPTION_MENU_STYLE"])
        self.dropdown.grid(row=8, column=0, pady=(0, 10), sticky="ew")

        self.delete_button = ctk.CTkButton(self.inner, text="삭제", width=240, command=self.delete_selected, **self.styles["BUTTON_DELETE_STYLE"])
        self.delete_button.grid(row=9, column=0, pady=(0, 30), sticky="ew")

        self.kor_to_eng = {}
        self.reload_dropdown()

    
    def reload_dropdown(self):
        product_data = load_products()
        self.kor_to_eng.clear()
        
        values = ["<-- Select -->"]
        for eng, info in product_data.get("product_list", {}).items():
            kor = info.get("must_include", "")
            self.kor_to_eng[kor] = eng
            values.append(kor)

        self.dropdown.configure(values=values)
        self.dropdown.set("<-- Select -->")

    def add_product(self):
        name = self.entry_product.get().strip().lower()
        keyword = self.entry_keyword.get().strip()
        if not name or not keyword:
            msg.showerror("Input Error", "Please enter both product name and keyword.")
            return
        product_data = load_products()
        product_list = product_data.get("product_list", {})
        if name in product_list:
            msg.showerror("Duplicated Error", f"Product already exists: {name}")
            return
        product_list[name] = {"product_name": name, "must_include": keyword}
        product_data["product_list"] = product_list
        save_products(product_data)
        msg.showinfo("Success", f"{name} has been added.")
        self.entry_product.delete(0, "end")
        self.entry_keyword.delete(0, "end")
        self.reload_dropdown()

    def delete_selected(self):
        korean = self.dropdown.get()
        
        if korean == "<-- Select -->":
            msg.showwarning("Error", "Select a product to delete.")
            return

        eng = self.kor_to_eng.get(korean)
        if not eng:
            msg.showerror("Error", "Could not find product information.")
            return

        success, msg_text = delete_product(eng)
        if success:
            msg.showinfo(f"Product {korean} deleted successfully", msg_text)
            self.reload_dropdown()
        else:
            msg.showerror("Delete Request Failed", msg_text)

# ────── App Class ──────
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


        # ────── Title Bar ──────
        self.title_bar = ctk.CTkFrame(self, height=50, fg_color="#f0f0f0")
        self.title_bar.grid(row=0, column=0, sticky="ew")
        self.title_bar.grid_columnconfigure(0, weight=1)

        self.title_label = ctk.CTkLabel(
            self.title_bar,
            text="Unzip Helper",
            **self.styles["FONT_TITLE"]
        )
        self.title_label.grid(row=0, column=0, padx=20, pady=(12, 8), sticky="w")

        # ────── Tab View ──────
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

        self.tab_exec.grid_columnconfigure(0, weight=1)
        self.tab_conf.grid_columnconfigure(0, weight=1)

        self.subframe1 = SubFrame1(self.tab_exec, self.styles)
        self.subframe1.grid(row=0, column=0, sticky="")

        self.subframe2 = SubFrame2(self.tab_conf, self.styles)
        self.subframe2.grid(row=0, column=0, sticky="")

        # ────── Footer + Log Box ──────
        self.footer_label = ctk.CTkLabel(self, text=f"Unzip Helper v{VERSION_INFO}", height=30, text_color="gray", font=self.styles["FONT_REGULAR"])
        self.footer_label.grid(row=2, column=0, pady=(0, 2), sticky="s")

        self.log_box = ctk.CTkTextbox(self, height=120, font=self.styles["FONT_REGULAR"])
        self.log_box.grid(row=3, column=0, padx=20, pady=(0, 10), sticky="ew")

        logu.init_logging()
        self.after(100, self.after_gui_loaded)

    def on_tab_change(self):
        current_tab = self.tabview.get()
        if current_tab == "Run":
            self.subframe1.reload_dropdown()

    def after_gui_loaded(self):
        sys.stdout = logu.InfoOnlyLogger(self.log_box)
        sys.stderr = logu.InfoOnlyLogger(self.log_box)
        log_user("Start Logging")
        log_debug("Debug also here!")
        print("[INFO] Manual info print")
        self.update_footer_label()
        self.subframe1.reload_dropdown()

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

    def show_subframe2(self):
        self.tabview.set("Add/Delete Products")

    def show_subframe1(self):
        self.tabview.set("Run")


# ────── Entry Point ──────
def main():
    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("green")
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
