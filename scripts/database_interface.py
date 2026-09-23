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
import yaml
from datetime import datetime
from pathlib import Path
import re
import sys
import subprocess


# ---------------------------------------------------------
# GLOBAL ROOT WINDOW
# ---------------------------------------------------------
root = tk.Tk()
root.title("Lake Kivu CTD Database")
#root.geometry("1200x700")
root.geometry("1400x900")
root.configure(bg="#CEE5FD")

# Enable minimize + maximize across all OS
root.resizable(True, True)
try:
    root.state('zoomed')              # Windows, some Linux
except:
    root.attributes('-zoomed', True)  # macOS fallback
# ---------------------------------------------------------
# CLEAR WINDOW FUNCTION (used everywhere)
# ---------------------------------------------------------
def clear_window():
    for widget in root.winfo_children():
        widget.destroy()

# Parent directory
PROJECT_DIR = Path(__file__).resolve().parent.parent
# ---------------------------------------------------------
# LOAD & ADD EXISTING METADATA PAGE
# ---------------------------------------------------------
def load_and_add_metadata_page():
    clear_window()

    bg_color = "#CEE5FD"

    title = tk.Label(
        root,
        text="Import and add existing metadata",
        font=("Arial", 32, "bold"),
        bg=bg_color,
        fg="black"
    )
    title.pack(pady=20)

    frame = tk.Frame(root, bg=bg_color)
    frame.pack(pady=40)
    btn_colors = ["#97B0CA", "#93C6FC", "white"]

    # --- Metadata file ---
    tk.Label(frame, text="Metadata Excel File:", font=("Arial", 18), bg=bg_color).grid(row=0, column=0, sticky="w", pady=10)
    metadata_entry = tk.Entry(frame, width=50, font=("Arial", 16))
    metadata_entry.grid(row=0, column=1, pady=10)

    def select_metadata():
        path = filedialog.askopenfilename(filetypes=[("Excel Files", "*.xlsx *.xls")])
        metadata_entry.delete(0, tk.END)
        metadata_entry.insert(0, path)

    tk.Button(
        frame,
        text="Browse",
        font=("Arial", 16),
        bg=btn_colors[0],
        fg=btn_colors[2],
        activebackground=btn_colors[1],
        activeforeground=btn_colors[2],
        relief="raised",
        bd=3,
        command=select_metadata
    ).grid(row=0, column=2, padx=10)

    # --- TOB directory ---
    tk.Label(frame, text="TOB Directory:", font=("Arial", 18), bg=bg_color).grid(row=1, column=0, sticky="w", pady=10)
    directory_entry = tk.Entry(frame, width=50, font=("Arial", 16))
    directory_entry.grid(row=1, column=1, pady=10)

    def select_directory():
        path = filedialog.askdirectory()
        directory_entry.delete(0, tk.END)
        directory_entry.insert(0, path)

    tk.Button(
        frame,
        text="Browse",
        font=("Arial", 16),
        bg=btn_colors[0],
        fg=btn_colors[2],
        activebackground=btn_colors[1],
        activeforeground=btn_colors[2],
        relief="raised",
        bd=3,
        command=select_directory
    ).grid(row=1, column=2, padx=10)


    # --- Years ---
    tk.Label(frame, text="Start Year:", font=("Arial", 18), bg=bg_color).grid(row=2, column=0, sticky="w", pady=10)
    start_year_entry = tk.Entry(frame, width=10, font=("Arial", 16))
    start_year_entry.grid(row=2, column=1, sticky="w")

    tk.Label(frame, text="End Year:", font=("Arial", 18), bg=bg_color).grid(row=3, column=0, sticky="w", pady=10)
    end_year_entry = tk.Entry(frame, width=10, font=("Arial", 16))
    end_year_entry.grid(row=3, column=1, sticky="w")

    # --- Run processing ---
    def run_processing():
        metadata_path = metadata_entry.get()
        tob_directory = directory_entry.get()
        start_year = start_year_entry.get()
        end_year = end_year_entry.get()

        check = input_quality_check(metadata_path, tob_directory, start_year, end_year)

        if check != "OK":
            popup = tk.Toplevel(root)
            popup.title("Input Error")
            popup.geometry("400x150")
            # Make popup modal
            popup.transient(root)     # keep on top of main window
            popup.grab_set()          # disable main window interaction
            tk.Label(popup, text=check, font=("Arial", 16), fg="red").pack(pady=20)
            tk.Button(popup, text="Close", font=("Arial", 14), command=popup.destroy).pack()
            popup.wait_window()
            return

        popup, progress = show_progress_popup()
        process_metadata_async(popup, progress, metadata_path, tob_directory, start_year, end_year)

    tk.Button(
        root,
        text="Run metadata processing >>>",
        font=("Arial", 18),
        bg="#97B0CA",
        fg="white",
        activebackground="#93C6FC",
        activeforeground="white",
        relief="raised",
        bd=3,
        command=run_processing
    ).place(x=900, y=840)

    add_back_button().place(x=50, y=840)

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



COLUMNS = [
    "Campaign_number:", "Profile_count:", "Profile:", "date:",
    "Latitude_S_(digital):", "Longitude_E_(digital):",
    "Distance_to_GEF_(m):", "Rope_length_(m):", "Max_depth_(m):",
    "TOB_name_in_Database:", "Purpose_of_sampling:",
    "pH_Calibration_(7):", "pH_Calibration_(9):",
    "pH_Calibration_(10):", "pH_Calibration_(4):"
]

# ---------------------------------------------------------
# CREATE NEW METADATA PAGE
# ---------------------------------------------------------
def create_new_metadata_page():
    clear_window()

    bg_color = "#CEE5FD"
    btn_colors = ["#97B0CA", "#93C6FC", "white"]

    title = tk.Label(
        root,
        text="Create New Metadata Entry",
        font=("Arial", 32, "bold"),
        bg=bg_color,
        fg="black"
    )
    title.pack(pady=20)

    form_frame = tk.Frame(root, bg=bg_color)
    form_frame.pack(pady=10)

    entries = {}

    # Create form fields
    for i, col in enumerate(COLUMNS):
        tk.Label(
            form_frame,
            text=col,
            font=("Arial", 16),
            bg=bg_color
        ).grid(row=i, column=0, sticky="w", pady=5)

        ent = tk.Entry(form_frame, width=40, font=("Arial", 16))
        ent.grid(row=i, column=1, pady=5)
        entries[col] = ent

    # ---------------------------------------------------------
    # SAVE PROFILE BUTTON (bottom-middle)
    # ---------------------------------------------------------
    def save_profile():
        messagebox.showinfo("Saved", "Profile saved (placeholder).")

    tk.Button(
        root,
        text="Save Profile",
        font=("Arial", 18),
        width=20,
        bg=btn_colors[0],
        fg=btn_colors[2],
        activebackground=btn_colors[1],
        activeforeground=btn_colors[2],
        relief="raised",
        bd=3,
        command=save_profile
    ).place(x=570, y=840)

    # ---------------------------------------------------------
    # SAVE METADATA BUTTON (bottom-right)
    # ---------------------------------------------------------
    def save_new_metadata():
        save_path = filedialog.asksaveasfilename(
            title="Save Metadata Excel File",
            defaultextension=".xlsx",
            filetypes=[("Excel Files", "*.xlsx")]
        )
        if not save_path:
            return

        data = {col: [entries[col].get()] for col in COLUMNS}
        df = pd.DataFrame(data)
        df.to_excel(save_path, index=False)

        messagebox.showinfo("Saved", "Metadata saved successfully.")

    tk.Button(
        root,
        text="Save Metadata >>>",
        font=("Arial", 18),
        width=20,
        bg=btn_colors[0],
        fg=btn_colors[2],
        activebackground=btn_colors[1],
        activeforeground=btn_colors[2],
        relief="raised",
        bd=3,
        command=save_new_metadata
    ).place(x=1080, y=840)

    # ---------------------------------------------------------
    # BACK BUTTON (bottom-left)
    # ---------------------------------------------------------
    add_back_button().place(x=50, y=840)

# ---------------------------------------------------------
#------------------- PROCESS & RUN DATABASE ---------------
# ---------------------------------------------------------
def run_process_database_page():
    clear_window()

    # =========================================================
    # Appearance
    # =========================================================
    bg_color = "#CEE5FD"
    frame_color = "#97B0CA"

    root.configure(bg=bg_color)

    # =========================================================
    # Window / layout parameters
    # =========================================================
    WINDOW_WIDTH = 1400
    WINDOW_HEIGHT = 900

    # ---- Main frames ----
    FRAME_Y = 180
    FRAME_HEIGHT = 540

    FRAME_LEFT = 40
    FRAME_RIGHT = 40
    FRAME_GAP = 20

    # ---- Bottom buttons ----
    BUTTON_Y = 820

    # =========================================================
    # Title
    # =========================================================
    tk.Label(
        root,
        text="Run & process database",
        font=("Arial", 36, "bold"),
        bg=bg_color,
        fg="black"
    ).place(
        relx=0.5,
        y=20,
        anchor="n"
    )

    # =========================================================
    # Calculate frame widths
    # =========================================================
    total_width = WINDOW_WIDTH - FRAME_LEFT - FRAME_RIGHT

    frame_width = (
        total_width - 2 * FRAME_GAP
    ) / 3

    # =========================================================
    # Frame definitions
    # =========================================================
    frame_titles = [
        "Required packages",
        "Database minimum date",
        "Required lake level data"
    ]

    for i, title_text in enumerate(frame_titles):

        x = FRAME_LEFT + i * (frame_width + FRAME_GAP)

        frame = tk.Frame(
            root,
            bg=frame_color,
            bd=3,
            relief="ridge"
        )

        frame.place(
            x=x,
            y=FRAME_Y,
            width=frame_width,
            height=FRAME_HEIGHT
        )

        # -----------------------------------------------------
        # Frame title
        # -----------------------------------------------------
        tk.Label(
            frame,
            text=title_text,
            font=("Arial", 20, "bold"),
            bg=frame_color,
            fg="black"
        ).pack(pady=(10, 5))

        # -----------------------------------------------------
        # Frame-specific content
        # -----------------------------------------------------

        # STEP 1: Required packages
        if i == 0:
            python_var = create_step1_packages(frame, frame_color)

            # step1_text = tk.Text(
            #     frame,
            #     font=("Arial", 14, "bold"),
            #     bg=frame_color,
            #     fg="white",
            #     wrap="word",
            #     height=4,
            #     width=1,
            #     bd=0,
            #     highlightthickness=0,
            #     spacing3=5
            # )

            # step1_text.pack(
            #     padx=35,
            #     pady=(120, 15),
            #     fill="x"
            # )

            # # Add the normal text
            # step1_text.insert(
            #     "end",
            #     "STEP 1: Make sure that all required packages "
            #     "(requirements.txt) are installed in your " 
            #     "active Python environment. "
            # )

            # # Add the hyperlink text
            # step1_text.insert("end", "See here.", "link")

            # # Define the hyperlink appearance
            # step1_text.tag_config(
            #     "link",
            #     foreground="blue",
            #     underline=True
            # )

            # # Make the hyperlink clickable
            # import webbrowser

            # step1_text.tag_bind(
            #     "link",
            #     "<Button-1>",
            #     lambda event: webbrowser.open("https://github.com/tdoda/lake-kivu-ctd-database/tree/master")
            # )

            # def update_cursor(event):
            #     index = step1_text.index(f"@{event.x},{event.y}")

            #     if "link" in step1_text.tag_names(index):
            #         step1_text.config(cursor="hand2")
            #     else:
            #         step1_text.config(cursor="arrow")


            # step1_text.bind("<Motion>", update_cursor)
            # # Prevent the user from editing the text
            # step1_text.config(state="disabled")

        # STEP 2: Minimum date
        elif i == 1:
            min_date_var = create_step2_min_date(frame, frame_color)

        # STEP 3: Lake level
        elif i == 2:

            pass

    # =========================================================
    # Bottom buttons
    # =========================================================
    tk.Button(
        root,
        text="Save & continue >>>",
        font=("Arial", 18),
        width=20,
        bg="#97B0CA",
        fg="white",
        activebackground="#93C6FC",
        activeforeground="white",
        relief="raised",
        bd=3,
        command=lambda: save_and_continue(min_date_var,python_var)
    ).place(x=1080,y=BUTTON_Y)

    add_back_button().place(
        x=50,
        y=BUTTON_Y
    )

def create_step1_packages(frame, frame_color):

    # ---------------------------------------------------------
    # Detect the Python environment currently running the GUI
    # ---------------------------------------------------------
    python_path = sys.executable
    #python_path = update_python_path_file()

    # ---------------------------------------------------------
    # STEP 1 explanatory text
    # ---------------------------------------------------------
    step1_text = tk.Text(
        frame,
        font=("Arial", 14, "bold"),
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
        padx=35,
        pady=(50, 15),
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

        index = step1_text.index(f"@{event.x},{event.y}")

        if "link" in step1_text.tag_names(index):
            step1_text.config(cursor="hand2")
        else:
            step1_text.config(cursor="arrow")

    step1_text.bind("<Motion>", update_cursor)

    # ---------------------------------------------------------
    # Prevent the user from editing the text
    # ---------------------------------------------------------
    step1_text.config(state="disabled")

    # ---------------------------------------------------------
    # Python environment
    # ---------------------------------------------------------
    tk.Label(
        frame,
        text="Python environment:",
        font=("Arial", 15, "bold"),
        bg=frame_color,
        fg="white"
    ).pack(
        padx=35,
        pady=(10, 5),
        anchor="w"
    )

    python_var = tk.StringVar(value=sys.executable)

    # Python path entry
    python_entry = tk.Entry(
        frame,
        textvariable=python_var,
        font=("Arial", 12),
        width=1,
        relief="sunken",
        bd=2,
        state="readonly",
        readonlybackground="white"
    )

    python_entry.pack(
        padx=35,
        pady=(0, 5),
        fill="x"
    )


    # ---------------------------------------------------------
    # Browse button
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
        font=("Arial", 14, "bold"),
        bg=frame_color,
        fg="white",
        activebackground=frame_color,
        activeforeground="white",
        relief="raised",
        bd=2,
        cursor="hand2"
    )

    browse_button.pack(
        padx=35,
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
    # Step 2 explanatory text
    # ---------------------------------------------------------
    step2_text = tk.Text(
        frame,
        font=("Arial", 14, "bold"),
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
        padx=35,
        pady=(70, 5),
        fill="x"
    )

    step2_text.insert(
        "end",
        "STEP 2: Define the minimum date for the database. "
        "Profiles collected before this date will not be included "
        "in the database."
    )

    step2_text.config(state="disabled")

    # ---------------------------------------------------------
    # Minimum date label
    # ---------------------------------------------------------
    tk.Label(
        frame,
        text="Minimum date:",
        font=("Arial", 16, "bold"),
        bg=frame_color,
        fg="white"
    ).pack(
        padx=35,
        pady=(15, 5),
        anchor="w"
    )
    # ---------------------------------------------------------
    # Date entry + Edit ON/OFF button
    # ---------------------------------------------------------
    date_var = tk.StringVar(value=min_date)
    date_edit_frame = tk.Frame(
        frame,
        bg=frame_color
    )

    date_edit_frame.pack(
        padx=35,
        pady=(0, 10),
        anchor="w"
    )

    # Date entry
    date_entry = tk.Entry(
        date_edit_frame,
        textvariable=date_var,
        font=("Arial", 16),
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

    # Edit ON/OFF button
    edit_var = tk.BooleanVar(value=False)

    def toggle_edit():

        if edit_var.get():

            # Editing ON
            date_entry.config(
                state="normal",
                bg="white",
                fg="black"
            )

            edit_button.config(
                text="edit"
            )

        else:

            # Editing OFF
            date_entry.config(
                state="readonly",
                readonlybackground="#B7C5D2",
                fg="#6F6F6F"
            )

            edit_button.config(
                text="edit"
            )


    edit_button = tk.Checkbutton(
        date_edit_frame,
        text="edit",
        variable=edit_var,
        command=toggle_edit,
        font=("Arial", 14, "bold"),
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
# HOMEPAGE
# ---------------------------------------------------------
def homepage():
    clear_window()

    bg_color = "#CEE5FD"

    title = tk.Label(
        root,
        text="Lake Kivu CTD Database",
        font=("Arial", 36, "bold"),
        bg=bg_color,
        fg="black"
    )
    title.pack(pady=20)

    subtitle = tk.Label(
        root,
        text="in-situ observations",
        font=("Arial", 16),
        bg=bg_color,
        fg="black"
    )
    subtitle.pack(pady=5)

    frame = tk.Frame(root, bg=bg_color)
    frame.pack(pady=80)

    btn_colors = ["#97B0CA", "#93C6FC", "white"]

    btn_load = tk.Button(
        frame,
        text="Load and add existing metadata",
        font=("Arial", 20),
        width=30,
        bg=btn_colors[0],
        fg=btn_colors[2],
        activebackground=btn_colors[1],
        activeforeground=btn_colors[2],
        relief="raised",
        bd=3,
        command=load_and_add_metadata_page
    )
    btn_load.grid(row=0, column=0, padx=20, pady=20)

    btn_new = tk.Button(
        frame,
        text="Create new metadata",
        font=("Arial", 20),
        width=30,
        bg=btn_colors[0],
        fg=btn_colors[2],
        activebackground=btn_colors[1],
        activeforeground=btn_colors[2],
        relief="raised",
        bd=3,
        command=create_new_metadata_page
    )
    btn_new.grid(row=1, column=0, padx=20, pady=20)

    btn_run_db = tk.Button(
        frame,
        text="Run & process database",
        font=("Arial", 20),
        width=30,
        bg=btn_colors[0],
        fg=btn_colors[2],
        activebackground=btn_colors[1],
        activeforeground=btn_colors[2],
        relief="raised",
        bd=3,
        command=run_process_database_page
    )
    btn_run_db.grid(row=2, column=0, padx=20, pady=20)

# ---------------------------------------------------------
# START APPLICATION
# ---------------------------------------------------------
if __name__ == "__main__":
    homepage()
    root.mainloop()