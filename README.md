# UnzipHelper 2.6.8

A lightweight desktop automation tool built with Python and CustomTkinter, designed to streamline batch file processing tasks such as unzipping files, converting images, and organizing outputs efficiently.
This tool was developed in response to requests from small teams working on Adobe After Effects templates, who needed a pre-workout file management solution. 
By automating repetitive tasks, it reduced the time required per zip file from approximately 5–15 minutes down to less than 1 minute, significantly improving productivity.


---

## Features
- Bulk unzip and folder structure handling
- Automatic image format conversion (e.g., HEIF → JPG)
- Real-time log window with safe UI updates
- Simple, clean GUI using CustomTkinter
- Configurable product/keyword management
- Diagnostics export for troubleshooting

---

## How It Works
1. **Select product keyword**
2. **Click "Run" to unzip and process files automatically**
3. **Logs update in real time as tasks progress**
4. **Export diagnostics for review if needed**

---

## Technical Highlights
- Python 3.11
- CustomTkinter for modern UI design
- Threading for non-blocking execution
- `after()` mechanism for thread-safe log updates in the UI
- Portable: works as `.exe` without requiring Python installed

---

## Folder Structure
```
UnzipHelper/
├── src/ # Source code root
│ ├── config/ # UI style config and static settings
│ │ ├── config.py # General app-level settings
│ │ ├── gui_config.py # GUI-specific size and layout configs
│ │ └── gui_styles.py # Centralized style/theme definitions
│ ├── utils/ # Utility modules for core features
│ │ ├── aep_utils.py # Utility functions for AEP file handling
│ │ ├── general_utils.py # General helper functions (e.g., file filtering)
│ │ ├── image_utils.py # Image format conversion helpers (e.g., HEIF → JPG)
│ │ ├── logging_utils.py # Centralized logging and log window updates
│ │ ├── product_store.py # JSON-based product/keyword storage and management
│ │ ├── resource_utils.py # Resource path resolution for bundled executable
│ │ ├── state.py # App-wide state management (global_state)
│ │ └── zip_utils.py # Core unzip logic and validation helpers
│ └── gui_main.py # Main GUI application entry point
├── assets/ # Static assets (icons, images, etc.)
│ └── unzip.ico # Application icon for Windows executable
└── README.md # Project description
```
---

## Why I built this
This project was developed to automate repetitive media processing workflows for small teams (e.g., photographers, editors) while providing transparency and reliability through a dedicated log interface.

---

## Build
Standalone executable created using PyInstaller (`--noconsole` mode) for Windows.
