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
            for processed, total, meta_files, lost_files, added in add_metadata_GUI(metadata_path, tob_directory, start_year, end_year):
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
        text="Save Metadata",
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

# ---------------------------------------------------------
# START APPLICATION
# ---------------------------------------------------------
if __name__ == "__main__":
    homepage()
    root.mainloop()