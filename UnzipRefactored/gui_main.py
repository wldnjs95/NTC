import customtkinter as ctk
import os
import config
import gui_config
from zip_utils import unzip_selected_files
from image_utils import convert_images_to_jpg

import sys
class PrintLogger:
    def __init__(self, textbox):
        self.textbox = textbox

    def write(self, message):
        self.textbox.insert("end", message)
        self.textbox.see("end")  # 스크롤 자동 이동

    def flush(self):  # for compatibility
        pass
    
    
def run_script():
    log_box.delete("1.0", "end")  # 실행 전 로그 초기화

    main_name = entry_main_folder.get().strip()
    keyword = entry_keyword.get().strip()

    has_error = False

    # Reset styles first
    entry_main_folder.configure(border_color="#D6F1FF")
    entry_keyword.configure(border_color="#D6F1FF")

    if not main_name:
        entry_main_folder.configure(border_color="red")
        has_error = True

    if not keyword:
        entry_keyword.configure(border_color="red")
        has_error = True

    if has_error:
        status_label.configure(text="⚠️ Warning: 모든 입력칸을 채워주세요", text_color="orange")
        return
    
    config.main_folder_name = main_name
    config.must_include = keyword
    
    status_label.configure(text="실행 중...", text_color="lightblue")
    

    try:
        start_dir = os.getcwd()
        unzip_selected_files(start_dir)
        for path in config.conversion_widths:
            convert_images_to_jpg(path, config.jpeg_quality)
        status_label.configure(text="Program Finished Successfully", text_color="green")
    except Exception as e:
        status_label.configure(text=f"⚠️ Error: {e}", text_color="red")

# GUI 설정
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("green")

app = ctk.CTk()
app.title("Unzip Helper")
app.geometry("480x540")
app.grid_columnconfigure(0, weight=1)


# ────── log box ──────
log_box = ctk.CTkTextbox(app, height=100, font=ctk.CTkFont(size=12))
log_box.grid(row=5, column=0, padx=30, pady=(0, 10), sticky="ew")

sys.stdout = PrintLogger(log_box)
sys.stderr = PrintLogger(log_box)



# ────── 제품 이름 섹션 ──────
product_frame = ctk.CTkFrame(app, fg_color="transparent")
product_frame.grid(row=0, column=0, padx=30, pady=(30, 0))

label_main = ctk.CTkLabel(
    product_frame,
    text="제품 이름",
    anchor="w",
    font=ctk.CTkFont(family="Apple SD Gothic Neo", size=12, weight="bold")
)
label_main.grid(row=0, column=0, sticky="w", padx=(3, 0))

entry_main_folder = ctk.CTkEntry(
    product_frame,
    placeholder_text="ex: Popcorn",
    width=gui_config.entry_width,
    height=gui_config.entry_height,
    justify="left",
    border_width=1
)
entry_main_folder.grid(row=1, column=0, sticky="w", pady=(5, 2))

desc_main = ctk.CTkLabel(
    product_frame,
    text="입력한 이름으로 작업 폴더가 생성됩니다.",
    text_color="gray",
    font=ctk.CTkFont(size=12),
    anchor="w"
)
desc_main.grid(row=2, column=0, sticky="w", padx=(9, 0), pady=(0, 10))

# ────── 키워드 섹션 ──────
keyword_frame = ctk.CTkFrame(app, fg_color="transparent")
keyword_frame.grid(row=1, column=0, padx=30)

label_keyword = ctk.CTkLabel(
    keyword_frame,
    text="키워드",
    anchor="w",
    font=ctk.CTkFont(family="Apple SD Gothic Neo", size=12, weight="bold")
)
label_keyword.grid(row=0, column=0, sticky="w", padx=(3, 0))

entry_keyword = ctk.CTkEntry(
    keyword_frame,
    placeholder_text="ex: (POPCORN)",
    width=gui_config.entry_width,
    height=gui_config.entry_height,
    justify="left",
    border_width=1
)
entry_keyword.grid(row=1, column=0, sticky="w", pady=(5, 2))

desc_keyword = ctk.CTkLabel(
    keyword_frame,
    text="해당 키워드를 포함한 압축파일만 처리됩니다.",
    text_color="gray",
    font=ctk.CTkFont(size=12),
    anchor="w"
)
desc_keyword.grid(row=2, column=0, sticky="w", padx=(9, 0), pady=(0, 10))

# ────── 실행 버튼 (중앙 정렬) ──────
run_button = ctk.CTkButton(app, text="실행", width=200, height=40, command=run_script)
run_button.grid(row=2, column=0, pady=20)

# ────── 상태 출력 라벨 (중앙 정렬) ──────
status_label = ctk.CTkLabel(app, text="", text_color="gray")
status_label.grid(row=3, column=0)

# ────── Footer  ──────
footer_label = ctk.CTkLabel(
    app,
    text="Unzip Helper v1.0",
    text_color="gray",
    font=ctk.CTkFont(size=12)
)
footer_label.grid(row=4, column=0, sticky="s", pady=(0, 10))

app.mainloop()