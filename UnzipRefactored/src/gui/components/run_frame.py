
# src/gui/components/run_frame.py
import customtkinter as ctk
import threading
import os
import tkinter.messagebox as msg

from src.core.file_operations import unzip_selected_files, convert_images_to_jpg, export_diagnostics, get_files_with_ext
from src.core.product_management import get_product_list, update_recent_product
from src.utils.logging_utils import log_user, log_debug, log_error
from src.config.config import DEMO_MODE, LIMIT_DAYS, LAUNCH_CUTOFF_DATE
import datetime
import shutil

class RunFrame(ctk.CTkFrame):
    def __init__(self, parent, styles):
        super().__init__(parent)
        self.styles = styles
        self.grid_columnconfigure((0, 2), weight=1)
        self.grid_columnconfigure(1, weight=0)
        self.configure(fg_color="#f9f9f9")

        self.product_dict = get_product_list()
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

        self.export_button = ctk.CTkButton(
            self,
            text="진단 파일 내보내기",
            width=220,
            command=self.export_diagnostics_ui,
            **self.styles["BUTTON_SECONDARY_STYLE"]
        )
        self.export_button.grid(row=4, column=1, pady=(0, 10))

    def export_diagnostics_ui(self):
        zip_path = export_diagnostics()
        subprocess.Popen(f'explorer /select,"{zip_path}"')

    def run_script(self):
        thread = threading.Thread(target=self.run_script_worker)
        thread.start()
        
    def run_script_worker(self):
        if DEMO_MODE:
            today = datetime.date.today()
            days_passed = (today - LAUNCH_CUTOFF_DATE).days
            if days_passed > LIMIT_DAYS:
                msg.showerror("Demo Expired", "New version required.")
                log_debug(f"[DEBUG] Demo expired. Days passed: {days_passed}, Limit: {LIMIT_DAYS}")
                self.status_label.configure(text="⛔ Demo Expired.", text_color="red")
                return
        
        global_state.conversion_targets = []
            
        selected_korean = self.dropdown.get()
        if selected_korean == self.placeholder:
            msg.showwarning("Selection Error", "Select a product to run.")
            return

        update_recent_product(selected_korean)
        product_name = self.must_include_map.get(selected_korean)
        product_info = self.product_dict.get(product_name)
        keyword = product_info["must_include"]

        global_state.product_name = product_name
        global_state.must_include = keyword

        try:
            aep_count = get_files_with_ext(os.getcwd(), '.aep')
            if len(aep_count) > 1:
                log_error(f"[CRITICAL] Multiple AEP files found in the current directory: {os.getcwd()}")
                raise RuntimeError("AEP 파일이 여러 개 있습니다. 하나만 있어야 합니다")
            elif len(aep_count) == 0:
                log_debug(f"No AEP file found in the current directory. Expected: {os.getcwd()}")
                raise RuntimeError(f"현재 디렉터리 {os.getcwd()}에 존재하는 AEP 파일이 없습니다")

            self.status_label.configure(text="Running...", text_color="lightblue")

            global_state.conversion_targets_mapping = {}
            success = unzip_selected_files(os.getcwd())
            if not success:
                self.status_label.configure(text="⛔ Unzip Failed.", text_color="red")
                return
            for path in global_state.conversion_targets_mapping.keys():
                if not os.path.exists(path):
                    log_error(f"[CRITICAL] Target directory does NOT exist: {path}")
                    raise FileNotFoundError(f"Target directory does NOT exist: {path}")
                else:
                    converted, errors = convert_images_to_jpg(path)
                    
                if errors > 0:
                    log_error(f"Conversion errors occurred in {path}.")
                    self.status_label.configure(text=f"⚠️ Conversion Errors: {errors}", text_color="red")
                    return
            
            log_debug(f"Conversion mapping image count: {len(global_state.conversion_targets_mapping)}")
            for original_folder in global_state.conversion_targets_mapping.keys():
                if os.path.exists(original_folder):
                    shutil.rmtree(original_folder)
                    log_debug(f"Deleted original folder: {original_folder}")

            self.status_label.configure(text="Completed Successfully.", text_color="green")
            log_user(f"프로그램 실행이 완료되었습니다. (키워드: {keyword})")
            
        except Exception as e:
            log_user(str(e))
            log_error(str(e))
            self.status_label.configure(text="⚠️ Error Occurred. Check Log", text_color="red")

    def reload_dropdown(self):
        self.product_dict = get_product_list()
        self.must_include_map = {}
        self.dropdown_values = [self.placeholder]
        for eng, info in self.product_dict.items():
            kor = info.get("must_include", "")
            self.dropdown_values.append(kor)
            self.must_include_map[kor] = eng
        self.dropdown.configure(values=self.dropdown_values)

        # Recent value handling
        recent_kor = self.recent_product
        if recent_kor in self.dropdown_values:
            self.dropdown.set(recent_kor)
        else:
            self.dropdown.set(self.placeholder)
