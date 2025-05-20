import customtkinter as ctk
import platform
import os
import config
from config import LIMIT_DAYS, LAUNCH_CUTOFF_DATE, DEMO_MODE
import gui_config
import json
import datetime
from zip_utils import unzip_selected_files
from image_utils import convert_images_to_jpg
import sys
import tkinter.messagebox as msg
import logging_utils as logu
from logging_utils import log_user, log_debug, log_error
from state import global_state

if platform.system() == "Windows":
    mono_font = "Consolas"
else:
    mono_font = "Menlo"


def after_gui_loaded():
    update_footer_label()

def update_footer_label():
    remaining_days = get_remaining_days()

    if remaining_days < 0:
        footer_label.configure(text="Unzip Helper v1.0  •  Invalid system date")
    elif not DEMO_MODE:
        footer_label.configure(text="Unzip Helper v1.0  •  (Official Version)")
    else:
        footer_label.configure(
            text=f"Unzip Helper v1.0\n( {remaining_days} days remaining )"
        )

def get_remaining_days():
    if not DEMO_MODE:
        log_debug("[Demo Mode :False]")
        return 999
    
    log_user("DEMO_MODE: True")
    today = datetime.date.today()
    days_passed = (today - LAUNCH_CUTOFF_DATE).days
    log_debug(f"Today: {today}, \nLaunch cutoff: {LAUNCH_CUTOFF_DATE},\nDays passed: {days_passed}")


    if days_passed < 0:
        msg.showerror("Error", "System date is incorrect. Please check your system date.")
        return -999
    
    remaining = LIMIT_DAYS - days_passed
    log_debug(f"Remaining days: {remaining}")
    return remaining



    
def run_script():
    #log_box.delete("1.0", "end")  # 실행 전 로그 초기화
    log_user("\n--------------------")
    log_user("실행 시작")
    
    global_state.conversion_widths = []
    global_state.product_name = entry_main_folder.get().strip()
    global_state.keyword = entry_keyword.get().strip()

    has_error = False

    # Reset styles first
    entry_main_folder.configure(border_color="#D6F1FF")
    entry_keyword.configure(border_color="#D6F1FF")

    if not global_state.product_name:
        entry_main_folder.configure(border_color="red")
        has_error = True

    if not global_state.keyword:
        entry_keyword.configure(border_color="red")
        has_error = True

    if has_error:
        status_label.configure(text="⚠️ Warning: 모든 입력칸을 채워주세요", text_color="orange")
        return
    
    
    status_label.configure(text="실행 중...", text_color="lightblue")
    

    try:
        start_dir = os.getcwd()
        unzip_selected_files(start_dir)
        for path in global_state.conversion_widths:
            convert_images_to_jpg(path, config.jpeg_quality)
        status_label.configure(text="Program Finished Successfully", text_color="green")
    except Exception as e:
        log_error(f"Error: {e}")
        status_label.configure(text=f"⚠️ Error: check app.log file", text_color="red")

# GUI 설정
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("green")

app = ctk.CTk()
app.title("Unzip Helper")
app.geometry("480x540")
app.grid_columnconfigure(0, weight=1)

# ────── 유저 입력 전체 프레임 ──────
input_frame = ctk.CTkFrame(app, fg_color="transparent")
input_frame.grid(row=0, column=0, padx=30, pady=(30, 0), sticky="n")
input_frame.grid_columnconfigure(0, weight=1)

# ────── 제품 이름 프레임 ──────
product_frame = ctk.CTkFrame(input_frame, fg_color="transparent")
product_frame.grid(row=0, column=0, pady=(0, 10), sticky="ew")

# ────── 키워드 프레임 ──────
keyword_frame = ctk.CTkFrame(input_frame, fg_color="transparent")
keyword_frame.grid(row=1, column=0, sticky="ew")



# ────── 제품 이름 섹션 ──────

label_main = ctk.CTkLabel(
    product_frame,
    text="제품 이름",
    anchor="w",
    font=ctk.CTkFont(family=mono_font, size=12, weight="bold")
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
    text="입력한 이름으로 내부 폴더와 AEP 파일명이 생성됩니다.",
    text_color="gray",
    font=ctk.CTkFont(size=12),
    anchor="w"
)
desc_main.grid(row=2, column=0, sticky="w", padx=(9, 0), pady=(0, 10))

# ────── 키워드 섹션 ──────

label_keyword = ctk.CTkLabel(
    keyword_frame,
    text="키워드",
    anchor="w",
    font=ctk.CTkFont(family=mono_font, size=12, weight="bold")
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
    text="Unzip Helper v1.0",  # 일단 기본값
    text_color="gray",
    font=ctk.CTkFont(size=12)
)
footer_label.grid(row=4, column=0, sticky="s", pady=(0, 10))


# ────── log box ──────
log_box = ctk.CTkTextbox(app, height=100, font=ctk.CTkFont(size=12))
log_box.grid(row=5, column=0, padx=30, pady=(10, 10), sticky="ew")

logu.init_logging()
sys.stdout = logu.DualLogger(log_box)
sys.stderr = logu.DualLogger(log_box)
# ────── GUI 로드 후 실행 ──────
app.after(100, after_gui_loaded if DEMO_MODE else lambda: None)
app.mainloop()