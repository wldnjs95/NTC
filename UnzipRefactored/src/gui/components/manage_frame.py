
# src/gui/components/manage_frame.py
import customtkinter as ctk
import tkinter.messagebox as msg
from src.core.product_management import get_product_list, add_product, remove_product

class ManageFrame(ctk.CTkFrame):
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

        self.add_button = ctk.CTkButton(self.inner, text="추가", width=240, command=self.add_product_ui, **self.styles["BUTTON_PRIMARY_STYLE"])
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
        product_data = get_product_list()
        self.kor_to_eng.clear()
        
        values = ["<-- Select -->"]
        for eng, info in product_data.items():
            kor = info.get("must_include", "")
            self.kor_to_eng[kor] = eng
            values.append(kor)

        self.dropdown.configure(values=values)
        self.dropdown.set("<-- Select -->")

    def add_product_ui(self):
        name = self.entry_product.get().strip().lower()
        keyword = self.entry_keyword.get().strip()
        if not name or not keyword:
            msg.showerror("Input Error", "Please enter both product name and keyword.")
            return
        
        success, message = add_product(name, keyword)
        if success:
            msg.showinfo("Success", message)
            self.entry_product.delete(0, "end")
            self.entry_keyword.delete(0, "end")
            self.reload_dropdown()
        else:
            msg.showerror("Error", message)

    def delete_selected(self):
        korean = self.dropdown.get()
        
        if korean == "<-- Select -->":
            msg.showwarning("Error", "Select a product to delete.")
            return

        eng = self.kor_to_eng.get(korean)
        if not eng:
            msg.showerror("Error", "Could not find product information.")
            return

        success, msg_text = remove_product(eng)
        if success:
            msg.showinfo(f"Product {korean} deleted successfully", msg_text)
            self.reload_dropdown()
        else:
            msg.showerror("Delete Request Failed", msg_text)
