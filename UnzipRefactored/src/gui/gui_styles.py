# gui_styles.py  (업데이트 버전)

import customtkinter as ctk


def get_styles():
    font_regular = ctk.CTkFont(family="Helvetica", size=13)
    font_bold    = ctk.CTkFont(family="Helvetica", size=13, weight="bold")
    font_small = ctk.CTkFont(family="Helvetica", size=11, weight="bold")

    FONT_TITLE = {
        "font": ctk.CTkFont(family="Helvetica", size=18, weight="bold"),
        "text_color": "#222222"
    }
    ENTRY_STYLE = {
        "font": font_regular,
        "height": 40,
        "corner_radius": 10,
        "border_width": 2,
        "border_color": "#c7c7c7",    
        "fg_color": "#ffffff",   
        "text_color": "#1c1c1e"
    }

    OPTION_MENU_STYLE = {
    "font": font_regular,
    "height": 30,
    "corner_radius": 6,
    "fg_color": "#D4D4D4",     
    "button_color": "#ABE9C5",
    "button_hover_color": "#92DCB1",
    "text_color": "#234838"
}

    BUTTON_PRIMARY_STYLE = {
        "font": font_bold,
        "height": 42,
        "corner_radius": 8,
        "fg_color": "#2CC985",
        "hover_color": "#29B87A",
        "text_color": "white"
    }

    BUTTON_DELETE_STYLE = {
        "font": font_bold,
        "height": 42,
        "corner_radius": 8,
        "fg_color": "#f36860",
        "hover_color": "#ec635c",
        "text_color": "white"
    }
    
    DESCRIPTION_STYLE = {
    "font": font_small,
    "text_color": "gray"
    }
    
    LABEL_STYLE = {
        "font": font_bold,
        "text_color": "#303030"
    }

    return {
        "FONT_REGULAR": font_regular,
        "FONT_BOLD": font_bold,
        "ENTRY_STYLE": ENTRY_STYLE,
        "OPTION_MENU_STYLE": OPTION_MENU_STYLE,
        "BUTTON_PRIMARY_STYLE": BUTTON_PRIMARY_STYLE,
        "BUTTON_DELETE_STYLE": BUTTON_DELETE_STYLE,
        "DESCRIPTION_STYLE": DESCRIPTION_STYLE,
        "LABEL_STYLE": LABEL_STYLE,
        "FONT_TITLE": FONT_TITLE
    }
