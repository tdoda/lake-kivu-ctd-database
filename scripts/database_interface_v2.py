# -*- coding: utf-8 -*-
"""
Created on Fri Sep 18 

@author: JeModeste
"""

import os
import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
from support_scripts.adding_meta_data import add_metadata_GUI
from support_scripts.visualize_database import load_level3_nc, plot_contour_nc, get_database_date_range, filter_visualization_data
import yaml
from datetime import datetime
from pathlib import Path
import re
import sys
import subprocess
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import yaml

# ============================================================
# GUI SETTINGS
# ============================================================

# Main window
WINDOW_TITLE = "Lake Kivu CTD Database"

WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 750

WINDOW_WIDTH_RATIO = 0.90
WINDOW_HEIGHT_RATIO = 0.90

MIN_WINDOW_WIDTH = 900
MIN_WINDOW_HEIGHT = 600

# Colors
BG_MAIN = "#CEE5FD"

BTN_BG = "#97B0CA"
BTN_ACTIVE_BG = "#93C6FC"
BTN_FG = "white"

# Fonts
FONT_FAMILY = "Arial"

FONT_TITLE = (FONT_FAMILY, 36, "bold")
FONT_SUBTITLE = (FONT_FAMILY, 16)
FONT_BUTTON = (FONT_FAMILY, 20)


# General spacing
PAD_X = 10
PAD_Y = 10

FRAME_PAD_X = 15
FRAME_PAD_Y = 10

FONT_PAGE_TITLE = (FONT_FAMILY, 32, "bold")
FONT_LABEL = (FONT_FAMILY, 18)
FONT_ENTRY = (FONT_FAMILY, 16)
FONT_SMALL_BUTTON = (FONT_FAMILY, 16)

# =========================================================
# GLOBAL VARIABLES
# =========================================================
PROJECT_DIR = Path(__file__).resolve().parent.parent
data_CTD = None

# =========================================================
# GENERAL GUI FUNCTIONS
# =========================================================
root = tk.Tk()

root.title(WINDOW_TITLE)
root.configure(bg=BG_MAIN)
root.resizable(True, True)

screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

window_width = min(WINDOW_WIDTH,int(screen_width * WINDOW_WIDTH_RATIO))

window_height = min(
    WINDOW_HEIGHT,
    int(screen_height * WINDOW_HEIGHT_RATIO)
)

root.geometry(
    f"{window_width}x{window_height}"
)

root.minsize(
    MIN_WINDOW_WIDTH,
    MIN_WINDOW_HEIGHT
)

# Enable minimize + maximize across all OS (full screen ------)
#root.resizable(True, True)
# try:
#     root.state('zoomed')              # Windows, some Linux
# except:
#     root.attributes('-zoomed', True)  # macOS fallback
# ---------------------------------------------------------
# CLEAR WINDOW FUNCTION (used everywhere)
# ---------------------------------------------------------
def clear_window():
    for widget in root.winfo_children():
        widget.destroy()

def close_application():
    print("Closing database ....")
    root.quit()
    root.destroy()

# =========================================================
# LOAD & ADD EXISTING METADATA
# =========================================================
def load_and_add_metadata_page():
    clear_window()

    # -----------------------------------------------------
    # Main frame
    # -----------------------------------------------------
    main_frame = tk.Frame(
        root,
        bg=BG_MAIN
    )

    main_frame.pack(
        fill="both",
        expand=True
    )

    # -----------------------------------------------------
    # Title
    # -----------------------------------------------------
    title = tk.Label(
        main_frame,
        text="Import and add existing metadata",
        font=FONT_PAGE_TITLE,
        bg=BG_MAIN,
        fg="black"
    )

    title.pack(
        pady=20
    )

    # -----------------------------------------------------
    # Form frame
    # -----------------------------------------------------
    form_frame = tk.Frame(
        main_frame,
        bg=BG_MAIN
    )

    form_frame.pack(
        fill="x",
        padx=PAD_X,
        pady=30
    )

    form_frame.grid_columnconfigure(0, weight=0)
    form_frame.grid_columnconfigure(1, weight=1)
    form_frame.grid_columnconfigure(2, weight=0)

    # -----------------------------------------------------
    # Metadata file
    # -----------------------------------------------------
    tk.Label(
        form_frame,
        text="Metadata Excel File:",
        font=FONT_LABEL,
        bg=BG_MAIN
    ).grid(
        row=0,
        column=0,
        sticky="w",
        padx=PAD_X,
        pady=PAD_Y
    )

    metadata_entry = tk.Entry(
        form_frame,
        font=FONT_ENTRY
    )

    metadata_entry.grid(
        row=0,
        column=1,
        sticky="ew",
        padx=PAD_X,
        pady=PAD_Y
    )

    def select_metadata():
        path = filedialog.askopenfilename(
            filetypes=[("Excel Files", "*.xlsx *.xls")]
        )

        metadata_entry.delete(0, tk.END)
        metadata_entry.insert(0, path)

    tk.Button(
        form_frame,
        text="Browse",
        font=FONT_SMALL_BUTTON,
        bg=BTN_BG,
        fg=BTN_FG,
        activebackground=BTN_ACTIVE_BG,
        activeforeground=BTN_FG,
        relief="raised",
        bd=3,
        command=select_metadata
    ).grid(
        row=0,
        column=2,
        padx=PAD_X,
        pady=PAD_Y
    )

    # -----------------------------------------------------
    # TOB directory
    # -----------------------------------------------------
    tk.Label(
        form_frame,
        text="TOB Directory:",
        font=FONT_LABEL,
        bg=BG_MAIN
    ).grid(
        row=1,
        column=0,
        sticky="w",
        padx=PAD_X,
        pady=PAD_Y
    )

    directory_entry = tk.Entry(
        form_frame,
        font=FONT_ENTRY
    )

    directory_entry.grid(
        row=1,
        column=1,
        sticky="ew",
        padx=PAD_X,
        pady=PAD_Y
    )

    def select_directory():
        path = filedialog.askdirectory()

        directory_entry.delete(0, tk.END)
        directory_entry.insert(0, path)

    tk.Button(
        form_frame,
        text="Browse",
        font=FONT_SMALL_BUTTON,
        bg=BTN_BG,
        fg=BTN_FG,
        activebackground=BTN_ACTIVE_BG,
        activeforeground=BTN_FG,
        relief="raised",
        bd=3,
        command=select_directory
    ).grid(
        row=1,
        column=2,
        padx=PAD_X,
        pady=PAD_Y
    )

    # -----------------------------------------------------
    # Start year
    # -----------------------------------------------------
    tk.Label(
        form_frame,
        text="Start Year:",
        font=FONT_LABEL,
        bg=BG_MAIN
    ).grid(
        row=2,
        column=0,
        sticky="w",
        padx=PAD_X,
        pady=PAD_Y
    )

    start_year_entry = tk.Entry(
        form_frame,
        width=10,
        font=FONT_ENTRY
    )

    start_year_entry.grid(
        row=2,
        column=1,
        sticky="w",
        padx=PAD_X,
        pady=PAD_Y
    )

    # -----------------------------------------------------
    # End year
    # -----------------------------------------------------
    tk.Label(
        form_frame,
        text="End Year:",
        font=FONT_LABEL,
        bg=BG_MAIN
    ).grid(
        row=3,
        column=0,
        sticky="w",
        padx=PAD_X,
        pady=PAD_Y
    )

    end_year_entry = tk.Entry(
        form_frame,
        width=10,
        font=FONT_ENTRY
    )

    end_year_entry.grid(
        row=3,
        column=1,
        sticky="w",
        padx=PAD_X,
        pady=PAD_Y
    )

    # -----------------------------------------------------
    # Run processing
    # -----------------------------------------------------
    def run_processing():

        metadata_path = metadata_entry.get()
        tob_directory = directory_entry.get()
        start_year = start_year_entry.get()
        end_year = end_year_entry.get()

        check = input_quality_check(
            metadata_path,
            tob_directory,
            start_year,
            end_year
        )

        if check != "OK":

            popup = tk.Toplevel(root)
            popup.title("Input Error")
            popup.geometry("400x150")

            popup.transient(root)
            popup.grab_set()

            tk.Label(
                popup,
                text=check,
                font=FONT_LABEL,
                fg="red"
            ).pack(pady=20)

            tk.Button(
                popup,
                text="Close",
                font=FONT_SMALL_BUTTON,
                command=popup.destroy
            ).pack()

            popup.wait_window()

            return

        popup, progress = show_progress_popup()

        process_metadata_async(
            popup,
            progress,
            metadata_path,
            tob_directory,
            start_year,
            end_year
        )

    # -----------------------------------------------------
    # Action frame
    # -----------------------------------------------------
    action_frame = tk.Frame(
        main_frame,
        bg=BG_MAIN
    )

    action_frame.pack(
        fill="x",
        padx=PAD_X,
        pady=30
    )

    action_frame.grid_columnconfigure(0, weight=1)
    action_frame.grid_columnconfigure(1, weight=1)

    # Back button
    back_button = add_back_button_new(action_frame)

    back_button.grid(
        row=0,
        column=0,
        sticky="w",
        padx=PAD_X
    )

    # Run button
    run_button = tk.Button(
        action_frame,
        text="Run metadata processing >>>",
        font=FONT_SMALL_BUTTON,
        bg=BTN_BG,
        fg=BTN_FG,
        activebackground=BTN_ACTIVE_BG,
        activeforeground=BTN_FG,
        relief="raised",
        bd=3,
        command=run_processing
    )

    run_button.grid(
        row=0,
        column=1,
        sticky="e",
        padx=PAD_X
    )

def input_quality_check(metadata_path, tob_directory, start_year, end_year):
    if not metadata_path:
        return "Metadata file path is missing."
    if not tob_directory:
        return "TOB directory is missing."
    if not start_year:
        return "Start year is missing."
    if not end_year:
        return "End year is missing."

    try:
        sy = int(start_year)
        ey = int(end_year)
    except:
        return "Start year and end year must be integers."

    if sy > ey:
        return "Start year must be less or equal to end year."

    if not os.path.isfile(metadata_path):
        return "Metadata file does not exist."

    if not os.path.isdir(tob_directory):
        return "TOB directory does not exist."

    return "OK"

def show_progress_popup(message="Processing metadata..."):
    popup = tk.Toplevel(root)
    popup.title(message)
    popup.geometry("400x300")

    popup.transient(root)
    popup.grab_set()

    tk.Label(popup, text=message, font=("Arial", 16)).pack(pady=10)

    progress = ttk.Progressbar(popup, mode="determinate", length=300)
    progress.pack(pady=10)

    return popup, progress


def process_metadata_async(popup, progress, metadata_path, tob_directory, start_year, end_year):

    def worker():
        try:
            # Initialize progress bar exactly like original
            progress["mode"] = "determinate"
            progress["value"] = 0

            for processed, total, meta_files, lost_files, added in add_metadata_GUI(
                metadata_path, tob_directory, start_year, end_year
            ):
                progress["maximum"] = total
                progress["value"] = processed
                popup.update_idletasks()

            tk.Label(popup, text="Done!", font=("Arial", 16), fg="green").pack(pady=10)

            summary_msg = (
                f"Metadata added: {added}\n"
                f"Existing metadata: {meta_files}\n"
                f"Lost files: {lost_files}"
            )
            tk.Label(popup, text=summary_msg, font=("Arial", 12)).pack(pady=10)

        except Exception as e:
            tk.Label(popup, text="Error processing metadata.", font=("Arial", 16), fg="red").pack(pady=10)
            tk.Label(popup, text=str(e), font=("Arial", 12)).pack()

    threading.Thread(target=worker).start()

# =========================================================
# CREATE NEW METADATA
# =========================================================

COLUMNS = [
    "Campaign_number:", "Profile_count:", "Profile:", "date:",
    "Latitude_S_(digital):", "Longitude_E_(digital):",
    "Distance_to_GEF_(m):", "Rope_length_(m):", "Max_depth_(m):",
    "TOB_name_in_Database:", "Purpose_of_sampling:",
    "pH_Calibration_(7):", "pH_Calibration_(9):",
    "pH_Calibration_(10):", "pH_Calibration_(4):"
]


def create_new_metadata_page():
    clear_window()

    # ---------------------------------------------------------
    # MAIN FRAME
    # ---------------------------------------------------------
    main_frame = tk.Frame(
        root,
        bg=BG_MAIN
    )

    main_frame.pack(
        fill="both",
        expand=True
    )

    # ---------------------------------------------------------
    # TITLE
    # ---------------------------------------------------------
    title = tk.Label(
        main_frame,
        text="Create New Metadata Entry",
        font=FONT_PAGE_TITLE,
        bg=BG_MAIN,
        fg="black"
    )

    title.pack(
        pady=(20, 10)
    )

    # ---------------------------------------------------------
    # SCROLLABLE FORM AREA
    # ---------------------------------------------------------

    # Container for canvas + scrollbar
    form_container = tk.Frame(
        main_frame,
        bg=BG_MAIN
    )

    form_container.pack(
        fill="both",
        expand=True,
        padx=PAD_X,
        pady=10
    )

    # Canvas
    canvas = tk.Canvas(
        form_container,
        bg=BG_MAIN,
        highlightthickness=0
    )

    canvas.pack(
        side="left",
        fill="both",
        expand=True
    )

    # Vertical scrollbar
    scrollbar = tk.Scrollbar(
        form_container,
        orient="vertical",
        command=canvas.yview
    )

    scrollbar.pack(
        side="right",
        fill="y"
    )

    canvas.configure(
        yscrollcommand=scrollbar.set
    )

    # Frame inside the canvas
    form_frame = tk.Frame(
        canvas,
        bg=BG_MAIN
    )

    # Add the form frame to the canvas
    canvas_window = canvas.create_window(
        (0, 0),
        window=form_frame,
        anchor="nw"
    )

    # ---------------------------------------------------------
    # MAKE THE FORM FRAME UPDATE ITS SCROLL REGION
    # ---------------------------------------------------------
    def update_scroll_region(event=None):
        canvas.configure(
            scrollregion=canvas.bbox("all")
        )

    form_frame.bind(
        "<Configure>",
        update_scroll_region
    )

    # ---------------------------------------------------------
    # MAKE THE FORM WIDTH FOLLOW THE CANVAS WIDTH
    # ---------------------------------------------------------
    def update_form_width(event):
        canvas.itemconfig(
            canvas_window,
            width=event.width
        )

    canvas.bind(
        "<Configure>",
        update_form_width
    )

    # ---------------------------------------------------------
    # FORM GRID
    # ---------------------------------------------------------
    form_frame.grid_columnconfigure(
        0,
        weight=0
    )

    form_frame.grid_columnconfigure(
        1,
        weight=1
    )

    entries = {}

    # ---------------------------------------------------------
    # CREATE FORM FIELDS
    # ---------------------------------------------------------
    for i, col in enumerate(COLUMNS):

        tk.Label(
            form_frame,
            text=col,
            font=FONT_LABEL,
            bg=BG_MAIN
        ).grid(
            row=i,
            column=0,
            sticky="w",
            padx=PAD_X,
            pady=5
        )

        ent = tk.Entry(
            form_frame,
            font=FONT_ENTRY
        )

        ent.grid(
            row=i,
            column=1,
            sticky="ew",
            padx=PAD_X,
            pady=5
        )

        entries[col] = ent

    # ---------------------------------------------------------
    # ACTION FRAME
    # ---------------------------------------------------------
    action_frame = tk.Frame(
        main_frame,
        bg=BG_MAIN
    )

    action_frame.pack(
        fill="x",
        padx=PAD_X,
        pady=15
    )

    action_frame.grid_columnconfigure(
        0,
        weight=1
    )

    action_frame.grid_columnconfigure(
        1,
        weight=1
    )

    action_frame.grid_columnconfigure(
        2,
        weight=1
    )

    # ---------------------------------------------------------
    # BACK BUTTON
    # ---------------------------------------------------------
    back_button = add_back_button_new(action_frame)

    back_button.grid(
        row=0,
        column=0,
        sticky="w",
        padx=PAD_X
    )

    # ---------------------------------------------------------
    # SAVE PROFILE BUTTON
    # ---------------------------------------------------------
    def save_profile():
        messagebox.showinfo(
            "Saved",
            "Profile saved (placeholder)."
        )

    save_profile_button = tk.Button(
        action_frame,
        text="Save Profile",
        font=FONT_SMALL_BUTTON,
        width=20,
        bg=BTN_BG,
        fg=BTN_FG,
        activebackground=BTN_ACTIVE_BG,
        activeforeground=BTN_FG,
        relief="raised",
        bd=3,
        command=save_profile
    )

    save_profile_button.grid(
        row=0,
        column=1,
        sticky="e",
        padx=PAD_X
    )

    # ---------------------------------------------------------
    # SAVE METADATA BUTTON
    # ---------------------------------------------------------
    def save_new_metadata():

        save_path = filedialog.asksaveasfilename(
            title="Save Metadata Excel File",
            defaultextension=".xlsx",
            filetypes=[("Excel Files", "*.xlsx")]
        )

        if not save_path:
            return

        data = {
            col: [entries[col].get()]
            for col in COLUMNS
        }

        df = pd.DataFrame(data)

        df.to_excel(
            save_path,
            index=False
        )

        messagebox.showinfo(
            "Saved",
            "Metadata saved successfully."
        )

    save_metadata_button = tk.Button(
        action_frame,
        text="Save Metadata >>>",
        font=FONT_SMALL_BUTTON,
        width=20,
        bg=BTN_BG,
        fg=BTN_FG,
        activebackground=BTN_ACTIVE_BG,
        activeforeground=BTN_FG,
        relief="raised",
        bd=3,
        command=save_new_metadata
    )

    save_metadata_button.grid(
        row=0,
        column=2,
        sticky="e",
        padx=PAD_X
    )

# ---------------------------------------------------------
# PROCESS & RUN DATABASE
# ---------------------------------------------------------
def run_process_database_page():
    clear_window()

    # =========================================================
    # MAIN FRAME
    # =========================================================
    main_frame = tk.Frame(
        root,
        bg=BG_MAIN
    )

    main_frame.pack(
        fill="both",
        expand=True
    )

    # =========================================================
    # TITLE
    # =========================================================
    title = tk.Label(
        main_frame,
        text="Run & process database",
        font=FONT_TITLE,
        bg=BG_MAIN,
        fg="black"
    )

    title.pack(
        pady=(20, 20)
    )

    # =========================================================
    # THREE MAIN FRAMES
    # =========================================================
    frames_container = tk.Frame(
        main_frame,
        bg=BG_MAIN
    )

    frames_container.pack(
        fill="both",
        expand=True,
        padx=PAD_X,
        pady=10
    )

    # Three equally sized columns
    frames_container.grid_columnconfigure(
        0,
        weight=1
    )

    frames_container.grid_columnconfigure(
        1,
        weight=1
    )

    frames_container.grid_columnconfigure(
        2,
        weight=1
    )

    # Allow the row to expand vertically
    frames_container.grid_rowconfigure(
        0,
        weight=1
    )

    # =========================================================
    # FRAME DEFINITIONS
    # =========================================================
    frame_titles = [
        "Required packages",
        "Database minimum date",
        "Required lake level data"
    ]

    for i, title_text in enumerate(frame_titles):

        frame = tk.Frame(
            frames_container,
            bg=BTN_BG,
            bd=3,
            relief="ridge"
        )

        frame.grid(
            row=0,
            column=i,
            sticky="nsew",
            padx=PAD_X
        )

        # -----------------------------------------------------
        # Frame title
        # -----------------------------------------------------
        tk.Label(
            frame,
            text=title_text,
            font=(FONT_FAMILY, 20, "bold"),
            bg=BTN_BG,
            fg="black"
        ).pack(
            pady=(10, 5)
        )

        # -----------------------------------------------------
        # Frame-specific content
        # -----------------------------------------------------

        # STEP 1: Required packages
        if i == 0:

            python_var = create_step1_packages(
                frame,
                BTN_BG
            )

        # STEP 2: Minimum date
        elif i == 1:

            min_date_var = create_step2_min_date(
                frame,
                BTN_BG
            )

        # STEP 3: Lake level
        elif i == 2:

            pass

    # =========================================================
    # BOTTOM ACTION FRAME
    # =========================================================
    action_frame = tk.Frame(
        main_frame,
        bg=BG_MAIN
    )

    action_frame.pack(
        fill="x",
        padx=PAD_X,
        pady=15
    )

    action_frame.grid_columnconfigure(
        0,
        weight=1
    )

    action_frame.grid_columnconfigure(
        1,
        weight=1
    )

    # =========================================================
    # BACK BUTTON
    # =========================================================
    back_button = add_back_button_new(
        action_frame
    )

    back_button.grid(
        row=0,
        column=0,
        sticky="w",
        padx=PAD_X
    )

    # =========================================================
    # SAVE & CONTINUE BUTTON
    # =========================================================
    continue_button = tk.Button(
        action_frame,
        text="Save & continue >>>",
        font=FONT_SMALL_BUTTON,
        width=20,
        bg=BTN_BG,
        fg=BTN_FG,
        activebackground=BTN_ACTIVE_BG,
        activeforeground=BTN_FG,
        relief="raised",
        bd=3,
        command=lambda: save_and_continue(
            min_date_var,
            python_var
        )
    )

    continue_button.grid(
        row=0,
        column=1,
        sticky="e",
        padx=PAD_X
    )

def create_step1_packages(frame, frame_color):

    # ---------------------------------------------------------
    # Detect the Python environment currently running the GUI
    # ---------------------------------------------------------
    python_path = sys.executable

    # ---------------------------------------------------------
    # STEP 1 explanatory text
    # ---------------------------------------------------------
    step1_text = tk.Text(
        frame,
        font=(FONT_FAMILY, 14, "bold"),
        bg=frame_color,
        fg="white",
        wrap="word",
        height=4,
        width=1,
        bd=0,
        highlightthickness=0,
        spacing2=3,
        spacing3=5
    )

    step1_text.pack(
        padx=PAD_X + 15,
        pady=(30, 15),
        fill="x"
    )

    # Normal text
    step1_text.insert(
        "end",
        "STEP 1: Make sure that all required packages "
        "(requirements.txt) are installed in your "
        "active Python environment. "
    )

    # Hyperlink text
    step1_text.insert(
        "end",
        "See here.",
        "link"
    )

    # ---------------------------------------------------------
    # Define hyperlink appearance
    # ---------------------------------------------------------
    step1_text.tag_config(
        "link",
        foreground="blue",
        underline=True
    )

    # ---------------------------------------------------------
    # Make hyperlink clickable
    # ---------------------------------------------------------
    import webbrowser

    step1_text.tag_bind(
        "link",
        "<Button-1>",
        lambda event: webbrowser.open(
            "https://github.com/tdoda/lake-kivu-ctd-database/tree/master"
        )
    )

    # ---------------------------------------------------------
    # Change cursor when hovering over hyperlink
    # ---------------------------------------------------------
    def update_cursor(event):

        index = step1_text.index(
            f"@{event.x},{event.y}"
        )

        if "link" in step1_text.tag_names(index):
            step1_text.config(cursor="hand2")
        else:
            step1_text.config(cursor="arrow")

    step1_text.bind(
        "<Motion>",
        update_cursor
    )

    # ---------------------------------------------------------
    # Prevent the user from editing the text
    # ---------------------------------------------------------
    step1_text.config(
        state="disabled"
    )

    # ---------------------------------------------------------
    # Python environment label
    # ---------------------------------------------------------
    tk.Label(
        frame,
        text="Python environment:",
        font=(FONT_FAMILY, 15, "bold"),
        bg=frame_color,
        fg="white"
    ).pack(
        padx=PAD_X + 15,
        pady=(10, 5),
        anchor="w"
    )

    # ---------------------------------------------------------
    # Python environment variable
    # ---------------------------------------------------------
    python_var = tk.StringVar(
        value=python_path
    )

    # ---------------------------------------------------------
    # Python path entry
    # ---------------------------------------------------------
    python_entry = tk.Entry(
        frame,
        textvariable=python_var,
        font=FONT_ENTRY,
        width=1,
        relief="sunken",
        bd=2,
        state="readonly",
        readonlybackground="white"
    )

    python_entry.pack(
        padx=PAD_X + 15,
        pady=(0, 5),
        fill="x"
    )

    # ---------------------------------------------------------
    # Browse Python executable
    # ---------------------------------------------------------
    def browse_python():

        path = filedialog.askopenfilename(
            title="Select Python executable"
        )

        if path:
            python_var.set(path)

    browse_button = tk.Button(
        frame,
        text="Browse",
        command=browse_python,
        font=FONT_SMALL_BUTTON,
        bg=frame_color,
        fg="white",
        activebackground=frame_color,
        activeforeground="white",
        relief="raised",
        bd=2,
        cursor="hand2"
    )

    browse_button.pack(
        padx=PAD_X + 15,
        pady=(5, 10),
        anchor="e"
    )

    return python_var

def create_step2_min_date(frame, frame_color):

    # ---------------------------------------------------------
    # Load minimum date from YAML
    # ---------------------------------------------------------
    config_file = Path(__file__).parent / "input_python.yaml"

    with open(config_file, "r") as f:
        config = yaml.safe_load(f)

    min_date = config["processing"]["min_date_period"]

    # ---------------------------------------------------------
    # STEP 2 explanatory text
    # ---------------------------------------------------------
    step2_text = tk.Text(
        frame,
        font=(FONT_FAMILY, 14, "bold"),
        bg=frame_color,
        fg="white",
        wrap="word",
        height=4,
        width=1,
        bd=0,
        highlightthickness=0,
        spacing3=5
    )

    step2_text.pack(
        padx=PAD_X + 15,
        pady=(40, 5),
        fill="x"
    )

    step2_text.insert(
        "end",
        "STEP 2: Define the minimum date for the database. "
        "Profiles collected before this date will not be included "
        "in the database."
    )

    step2_text.config(
        state="disabled"
    )

    # ---------------------------------------------------------
    # Minimum date label
    # ---------------------------------------------------------
    tk.Label(
        frame,
        text="Minimum date:",
        font=(FONT_FAMILY, 16, "bold"),
        bg=frame_color,
        fg="white"
    ).pack(
        padx=PAD_X + 15,
        pady=(15, 5),
        anchor="w"
    )

    # ---------------------------------------------------------
    # Date variable
    # ---------------------------------------------------------
    date_var = tk.StringVar(
        value=min_date
    )

    # ---------------------------------------------------------
    # Date entry + edit control
    # ---------------------------------------------------------
    date_edit_frame = tk.Frame(
        frame,
        bg=frame_color
    )

    date_edit_frame.pack(
        padx=PAD_X + 15,
        pady=(0, 10),
        fill="x"
    )

    # ---------------------------------------------------------
    # Date entry
    # ---------------------------------------------------------
    date_entry = tk.Entry(
        date_edit_frame,
        textvariable=date_var,
        font=FONT_ENTRY,
        width=15,
        justify="center",
        state="readonly",
        readonlybackground="#B7C5D2",
        fg="#6F6F6F",
        relief="sunken",
        bd=2
    )

    date_entry.pack(
        side="left"
    )

    # ---------------------------------------------------------
    # Edit ON/OFF variable
    # ---------------------------------------------------------
    edit_var = tk.BooleanVar(
        value=False
    )

    # ---------------------------------------------------------
    # Toggle editing
    # ---------------------------------------------------------
    def toggle_edit():

        if edit_var.get():

            # Editing ON
            date_entry.config(
                state="normal",
                bg="white",
                fg="black"
            )

        else:

            # Editing OFF
            date_entry.config(
                state="readonly",
                readonlybackground="#B7C5D2",
                fg="#6F6F6F"
            )

    # ---------------------------------------------------------
    # Edit checkbox
    # ---------------------------------------------------------
    edit_button = tk.Checkbutton(
        date_edit_frame,
        text="edit",
        variable=edit_var,
        command=toggle_edit,
        font=FONT_SMALL_BUTTON,
        bg=frame_color,
        fg="white",
        activebackground=frame_color,
        activeforeground="white",
        selectcolor=frame_color,
        cursor="hand2"
    )

    edit_button.pack(
        side="left",
        padx=(15, 0)
    )

    return date_var

# update python path automatically
def save_python_path(python_var):

    python_path = python_var.get().strip()

    if not python_path:
        messagebox.showerror(
            "Invalid Python path",
            "Please select a Python executable."
        )
        return False

    python_path_file = PROJECT_DIR / "python_path.txt"

    python_path_file.write_text(
        python_path,
        encoding="utf-8"
    )

    return True

    return sys.executable

def save_min_date_to_yaml(min_date_var):
    """
    Validate and save the minimum date from the GUI
    back to input_python.yaml.
    """

    new_date = min_date_var.get().strip()

    # Check that the date has the correct format
    try:
        datetime.strptime(new_date, "%Y-%m-%d")
    except ValueError:
        tk.messagebox.showerror(
            "Invalid date",
            "Please enter the minimum date in the format YYYY-MM-DD."
        )
        return False

    # Locate YAML file
    config_file = Path(__file__).parent / "input_python.yaml"

    # Read the existing YAML file
    with open(config_file, "r") as f:
        content = f.read()

    # Replace only the min_date_period line
    new_content = re.sub(
        r'(^\s*min_date_period:\s*")[^"]*(")',
        rf'\g<1>{new_date}\g<2>',
        content,
        flags=re.MULTILINE
    )

    # Write the updated YAML
    with open(config_file, "w") as f:
        f.write(new_content)

    return True

# start main_ctd_database for processing
def start_processing_gui():
    python_path = (PROJECT_DIR / "python_path.txt").read_text().strip()
    subprocess.Popen([python_path,str(PROJECT_DIR / "scripts" / "main_ctd_database.py")])

# validate user inputs and start processing the db
def save_and_continue(min_date_var, python_var):
    if not save_min_date_to_yaml(min_date_var):
        return
    if not save_python_path(python_var):
        return
    start_processing_gui()

#===========================================================================
# Functions for visualization (out of the class) ---------------------------
#===========================================================================
def get_database():
    global data_CTD
    if data_CTD is None:
        config_file = Path(__file__).resolve().parent / "input_python.yaml"
        with open(config_file, "r") as f:
            config = yaml.safe_load(f)
        directories = config["directories"]
        #database_file = (config_file.parent / directories["Level3_dir"] / "Combined" / "L3_comb.nc").resolve()
        database_file = "/storage/lakekivu/1D_Model/WP_workspaces/WP2/db_workspace/database_runs/full_database/L3_comb.nc"
        data_CTD = load_level3_nc(database_file)
    return data_CTD

def prepare_visualization():
    loading_label = show_loading_screen(
        "Loading database..."
    )

    def worker():

        data = get_database()

        min_date, max_date = get_database_date_range(
            data
        )
        data_plot = filter_visualization_data(
            data,
            min_date,
            max_date,
            0
        )

        root.after(
            0,
            lambda: start_initial_plot(
                data,
                data_plot,
                min_date,
                max_date,
                loading_label
            )
        )

    threading.Thread(
        target=worker,
        daemon=True
    ).start()

def start_initial_plot(
    data_CTD,
    data_plot,
    min_date,
    max_date,
    loading_label):

    global visualization_page

    # Remove the full-window loading screen first
    loading_label.master.destroy()

    visualization_page = VisualizationPage(
        data_CTD,
        min_date,
        max_date
    )

    visualization_page.show_visualization_page(
        clear=True
    )

    visualization_page.create_initial_plot(
        data_plot
    )

class VisualizationPage:

    def __init__(
        self,
        data_CTD,
        min_date,
        max_date):

        self.data_CTD = data_CTD

        self.min_date = min_date
        self.max_date = max_date

        self.fig = None
        self.ax = None
        self.canvas = None

        self.parameter_var = None
        self.start_date_var = None
        self.end_date_var = None
        self.z_below_var = None

        self.parameter_menu = None

        self.control_frame = None
        self.plot_frame = None

    # Fnction 1

    def show_visualization_page(self, clear=True):

        if clear:
            clear_window()

        # =========================================================
        # MAIN FRAME
        # =========================================================
        main_frame = tk.Frame(
            root,
            bg=BG_MAIN
        )

        main_frame.pack(
            fill="both",
            expand=True
        )

        # =========================================================
        # TITLE
        # =========================================================
        title = tk.Label(
            main_frame,
            text="Visualize Lake Kivu Database",
            font=FONT_PAGE_TITLE,
            bg=BG_MAIN,
            fg="black"
        )

        title.pack(
            pady=(20, 15)
        )

        # =========================================================
        # VISUALIZATION FRAME
        # =========================================================
        visualization_frame = tk.Frame(
            main_frame,
            bg=BTN_BG,
            relief="groove",
            bd=2
        )

        visualization_frame.pack(
            fill="both",
            expand=True,
            padx=PAD_X + 20,
            pady=10
        )

        # =========================================================
        # TWO-COLUMN LAYOUT
        # =========================================================

        # Control panel gets a fixed/preferred width.
        visualization_frame.grid_columnconfigure(
            0,
            weight=0
        )

        # Plot area gets all remaining horizontal space.
        visualization_frame.grid_columnconfigure(
            1,
            weight=1
        )

        # Both control panel and plot expand vertically.
        visualization_frame.grid_rowconfigure(
            0,
            weight=1
        )

        # =========================================================
        # CONTROL FRAME
        # =========================================================
        self.control_frame = tk.Frame(
            visualization_frame,
            bg=BTN_BG,
            relief="groove",
            bd=2,
            width=300
        )

        self.control_frame.grid(
            row=0,
            column=0,
            sticky="ns",
            padx=(15, 10),
            pady=15
        )

        # Prevent the control frame from being forced wider
        # by the grid.
        self.control_frame.grid_propagate(False)

        # =========================================================
        # PLOT FRAME
        # =========================================================
        self.plot_frame = tk.Frame(
            visualization_frame,
            bg="white",
            relief="sunken",
            bd=2
        )

        self.plot_frame.grid(
            row=0,
            column=1,
            sticky="nsew",
            padx=(0, 15),
            pady=15
        )

        # =========================================================
        # PLOT STATUS LABEL
        # =========================================================
        self.plot_status_label = tk.Label(
            self.plot_frame,
            text="",
            font=FONT_SMALL_BUTTON,
            bg="white",
            fg="#555555"
        )

        # =========================================================
        # CREATE CONTROLS
        # =========================================================
        self.create_visualization_controls()

        # =========================================================
        # CREATE BUTTONS
        # =========================================================
        self.create_visualization_buttons()

    # Function 2
    def create_visualization_controls(self):

        frame = self.control_frame
        frame_color = BTN_BG

        # =========================================================
        # PARAMETER
        # =========================================================

        tk.Label(
            frame,
            text="Parameter:",
            font=FONT_LABEL,
            bg=frame_color,
            fg="white"
        ).pack(
            padx=PAD_X + 10,
            pady=(15, 5),
            anchor="w"
        )

        self.parameter_var = tk.StringVar(
            value="Temperature"
        )

        self.parameter_menu = ttk.Combobox(
            frame,
            textvariable=self.parameter_var,
            values=[
                "Temperature",
                "Salinity",
                "Density"
            ],
            state="readonly",
            font=FONT_ENTRY
        )

        self.parameter_menu.pack(
            padx=PAD_X + 10,
            pady=(0, 20),
            fill="x"
        )

        self.parameter_menu.bind(
            "<<ComboboxSelected>>",
            self.update_visualization_parameter
        )

        # =========================================================
        # START DATE
        # =========================================================

        tk.Label(
            frame,
            text="From:",
            font=FONT_LABEL,
            bg=frame_color,
            fg="white"
        ).pack(
            padx=PAD_X + 10,
            pady=(5, 5),
            anchor="w"
        )

        self.start_date_var = tk.StringVar(
            value=self.min_date
        )

        tk.Entry(
            frame,
            textvariable=self.start_date_var,
            font=FONT_ENTRY,
            justify="center"
        ).pack(
            padx=PAD_X + 10,
            pady=(0, 15),
            fill="x"
        )

        # =========================================================
        # END DATE
        # =========================================================

        tk.Label(
            frame,
            text="To:",
            font=FONT_LABEL,
            bg=frame_color,
            fg="white"
        ).pack(
            padx=PAD_X + 10,
            pady=(5, 5),
            anchor="w"
        )

        self.end_date_var = tk.StringVar(
            value=self.max_date
        )

        tk.Entry(
            frame,
            textvariable=self.end_date_var,
            font=FONT_ENTRY,
            justify="center"
        ).pack(
            padx=PAD_X + 10,
            pady=(0, 15),
            fill="x"
        )

        # =========================================================
        # Z-BELOW
        # =========================================================

        tk.Label(
            frame,
            text="z-below [m]:",
            font=FONT_LABEL,
            bg=frame_color,
            fg="white"
        ).pack(
            padx=PAD_X + 10,
            pady=(5, 5),
            anchor="w"
        )

        self.z_below_var = tk.StringVar(
            value="0"
        )

        tk.Entry(
            frame,
            textvariable=self.z_below_var,
            font=FONT_ENTRY,
            justify="center"
        ).pack(
            padx=PAD_X + 10,
            pady=(0, 15),
            fill="x"
        )

    # Function 3
    def create_initial_plot(self, data_plot):

        self.show_plot_status("Plotting...")

        self.fig, self.ax = plot_contour_nc(
            data_plot,
            par="Temperature",
            dmin=0
        )

        self.canvas = FigureCanvasTkAgg(
            self.fig,
            master=self.plot_frame
        )

        self.canvas.draw()

        self.canvas.get_tk_widget().pack(
            fill="both",
            expand=True
        )

        self.plot_status_label.lift()

        root.update_idletasks()

        self.hide_plot_status()

    # Function 4
    def show_plot_status(self, message):

        self.plot_status_label.config(
            text=message
        )

        self.plot_status_label.place(
            relx=0.5,
            rely=0.5,
            anchor="center"
        )

        self.plot_status_label.lift()

        root.update_idletasks()

    # Function 5
    def hide_plot_status(self):
        self.plot_status_label.place_forget()

    # Function 6
    def update_visualization_parameter(self, event=None):

        parameter = self.parameter_var.get()

        start_date = self.start_date_var.get()
        end_date = self.end_date_var.get()

        try:

            z_below = float(
                self.z_below_var.get()
            )

        except ValueError:

            messagebox.showerror(
                "Invalid depth",
                "Please enter a valid number for z-below."
            )

            return

        self.show_plot_status(
            "Updating plot..."
        )

        self.parameter_menu.config(
            state="disabled"
        )

        worker = threading.Thread(
            target=self._prepare_parameter_data,
            args=(
                parameter,
                start_date,
                end_date,
                z_below
            ),
            daemon=True
        )

        worker.start()

    # Function 7
    def _prepare_parameter_data(
        self,
        parameter,
        start_date,
        end_date,
        z_below
    ):

        data_plot = filter_visualization_data(
            self.data_CTD,
            start_date,
            end_date,
            z_below
        )

        root.after(
            0,
            lambda: self._display_parameter_plot(
                data_plot,
                parameter
            )
        )

    # Function 8
    def _display_parameter_plot(
        self,
        data_plot,
        parameter):

        fig, ax = plot_contour_nc(
            data_plot,
            par=parameter,
            dmin=0
        )

        if self.canvas is not None:
            self.canvas.get_tk_widget().destroy()

        self.fig = fig
        self.ax = ax

        self.canvas = FigureCanvasTkAgg(
            self.fig,
            master=self.plot_frame
        )

        canvas_widget = self.canvas.get_tk_widget()

        canvas_widget.pack(
            fill="both",
            expand=True
        )

        self.canvas.draw()

        self.plot_frame.update_idletasks()

        root.after(
            50,
            self._finish_plot_update
        )

    # Function 9
    def _finish_plot_update(self):
        self.hide_plot_status()
        self.parameter_menu.config(
            state="readonly"
        )

    # Function 10
    def create_visualization_buttons(self):

        # =========================================================
        # ACTION FRAME
        # =========================================================

        action_frame = tk.Frame(
            root,
            bg=BG_MAIN
        )

        action_frame.pack(
            fill="x",
            padx=PAD_X + 20,
            pady=(0, 15)
        )

        action_frame.grid_columnconfigure(
            0,
            weight=1
        )

        action_frame.grid_columnconfigure(
            1,
            weight=1
        )

        # =========================================================
        # BACK BUTTON
        # =========================================================

        back_button = add_back_button_new(action_frame)

        back_button.grid(
            row=0,
            column=0,
            sticky="w",
            padx=PAD_X
        )

        # =========================================================
        # EXTRACT BUTTON
        # =========================================================

        extract_button = tk.Button(
            action_frame,
            text="Extract & save data",
            font=FONT_SMALL_BUTTON,
            width=20,
            bg=BTN_BG,
            fg=BTN_FG,
            activebackground=BTN_ACTIVE_BG,
            activeforeground=BTN_FG,
            relief="raised",
            bd=3
            # command=self.extract_and_save_data
        )

        extract_button.grid(
            row=0,
            column=1,
            sticky="e",
            padx=PAD_X
        )

 
def show_loading_screen(message):

    clear_window()

    # =========================================================
    # MAIN FRAME
    # =========================================================

    main_frame = tk.Frame(
        root,
        bg=BG_MAIN
    )

    main_frame.pack(
        fill="both",
        expand=True
    )

    # =========================================================
    # LOADING MESSAGE
    # =========================================================

    loading_label = tk.Label(
        main_frame,
        text=message,
        font=FONT_LABEL,
        bg=BG_MAIN,
        fg="black"
    )

    loading_label.pack(
        expand=True
    )

    root.update_idletasks()

    return loading_label

def create_visualization_buttons():

    add_back_button().place(x=40,y=820)

    tk.Button(
        root,
        text="Extract & save data",
        font=("Arial", 18),
        width=20,
        bg="#97B0CA",
        fg="white",
        activebackground="#93C6FC",
        activeforeground="white",
        relief="raised",
        bd=3#,
        #command=extract_and_save_data
    ).place(x=1080,y=820)


# ---------------------------------------------------------
# BACK BUTTON (standalone reusable)
# ---------------------------------------------------------
def add_back_button():
    btn_colors = ["#97B0CA", "#93C6FC", "white"]
    btn_back = tk.Button(
        root,
        text="<<< Back",
        font=("Arial", 16),
        bg=btn_colors[0],
        fg=btn_colors[2],
        activebackground=btn_colors[1],
        activeforeground=btn_colors[2],
        relief="raised",
        bd=3,
        command=homepage
    )
    return btn_back

# ---------------------------------------------------------
# BACK BUTTON (standalone reusable)
# ---------------------------------------------------------
def add_back_button_new(parent):

    btn_back = tk.Button(
        parent,
        text="<<< Back",
        font=FONT_SMALL_BUTTON,
        bg=BTN_BG,
        fg=BTN_FG,
        activebackground=BTN_ACTIVE_BG,
        activeforeground=BTN_FG,
        relief="raised",
        bd=3,
        command=homepage
    )

    return btn_back

# ---------------------------------------------------------
# HOMEPAGE
# ---------------------------------------------------------
def homepage():
    clear_window()

    # ---------------------------------------------------------
    # Main frame
    # ---------------------------------------------------------
    main_frame = tk.Frame(
        root,
        bg=BG_MAIN
    )

    main_frame.pack(
        fill="both",
        expand=True
    )

    # ---------------------------------------------------------
    # Title
    # ---------------------------------------------------------
    title = tk.Label(
        main_frame,
        text="Lake Kivu CTD Database",
        font=FONT_TITLE,
        bg=BG_MAIN,
        fg="black"
    )
    title.pack(pady=(30, 5))

    # ---------------------------------------------------------
    # Subtitle
    # ---------------------------------------------------------
    subtitle = tk.Label(
        main_frame,
        text="in-situ observations",
        font=FONT_SUBTITLE,
        bg=BG_MAIN,
        fg="black"
    )
    subtitle.pack(pady=(0, 30))

    # ---------------------------------------------------------
    # Button frame
    # ---------------------------------------------------------
    button_frame = tk.Frame(
        main_frame,
        bg=BG_MAIN
    )

    button_frame.pack(pady=20)

    # -----------------------------------------------------
    # Buttons
    # -----------------------------------------------------
    btn_colors = ["#97B0CA", "#93C6FC", "white"]

    btn_load = tk.Button(
        button_frame,
        text="Load and add existing metadata",
        font=FONT_BUTTON,
        width=30,
        bg=btn_colors[0],
        fg=btn_colors[2],
        activebackground=btn_colors[1],
        activeforeground=btn_colors[2],
        relief="raised",
        bd=3,
        command=load_and_add_metadata_page
    )
    btn_load.grid(
        row=0,
        column=0,
        padx=20,
        pady=10
    )

    btn_new = tk.Button(
        button_frame,
        text="Create new metadata",
        font=FONT_BUTTON,
        width=30,
        bg=btn_colors[0],
        fg=btn_colors[2],
        activebackground=btn_colors[1],
        activeforeground=btn_colors[2],
        relief="raised",
        bd=3,
        command=create_new_metadata_page
    )
    btn_new.grid(
        row=1,
        column=0,
        padx=20,
        pady=10
    )

    btn_run_db = tk.Button(
        button_frame,
        text="Run & process database",
        font=FONT_BUTTON,
        width=30,
        bg=btn_colors[0],
        fg=btn_colors[2],
        activebackground=btn_colors[1],
        activeforeground=btn_colors[2],
        relief="raised",
        bd=3,
        command=run_process_database_page
    )
    btn_run_db.grid(
        row=2,
        column=0,
        padx=20,
        pady=10
    )

    btn_visualize = tk.Button(
        button_frame,
        text="Visualize database",
        font=FONT_BUTTON,
        width=30,
        bg=btn_colors[0],
        fg=btn_colors[2],
        activebackground=btn_colors[1],
        activeforeground=btn_colors[2],
        relief="raised",
        bd=3,
        command=prepare_visualization
    )
    btn_visualize.grid(
        row=3,
        column=0,
        padx=20,
        pady=10
    )

# ---------------------------------------------------------
# START APPLICATION
# ---------------------------------------------------------
if __name__ == "__main__":

    root.protocol(
        "WM_DELETE_WINDOW",
        close_application
    )

    homepage()
    root.mainloop()