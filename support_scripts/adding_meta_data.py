# -*- coding: utf-8 -*-
"""
Created on Tue Mar 29 11:00:10 2022

@author: thomitob
"""

import os
import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import time


# ---------------------------------------------------------
# GLOBAL ROOT WINDOW
# ---------------------------------------------------------
root = tk.Tk()
root.title("Lake Kivu CTD Database")
root.geometry("1200x700")
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
    ).place(x=900, y=640)

    add_back_button()

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
            sy = int(start_year)
            ey = int(end_year)

            # ---------------------------------------------------------
            # 1. Count total rows across all selected years
            # ---------------------------------------------------------
            total_rows = 0
            for year in range(sy, ey + 1):
                df = pd.read_excel(metadata_path, sheet_name=str(year),
                                   engine='openpyxl', header=None, skiprows=2)
                df = df.iloc[:, :15]
                total_rows += len(df)

            # ---------------------------------------------------------
            # 2. Configure progress bar for determinate mode
            # ---------------------------------------------------------
            progress["mode"] = "determinate"
            progress["maximum"] = total_rows
            progress["value"] = 0

            # ---------------------------------------------------------
            # 3. Process metadata row-by-row
            # ---------------------------------------------------------
            meta_files = 0
            lost_files = 0
            added = 0

            for year in range(sy, ey + 1):
                df = pd.read_excel(metadata_path, sheet_name=str(year),
                                   engine='openpyxl', header=None, skiprows=2)
                df = df.iloc[:, :15]
                df.columns = [
                    "Campaign_number:", "Profile_count:", "Profile:", "date:",
                    "Latitude_S_(digital):", "Longitude_E_(digital):",
                    "Distance_to_GEF_(m):", "Rope_length_(m):", "Max_depth_(m):",
                    "TOB_name_in_Database:", "Purpose_of_sampling:",
                    "pH_Calibration_(7):", "pH_Calibration_(9):",
                    "pH_Calibration_(10):", "pH_Calibration_(4):"
                ]

                for index, row in df.iterrows():
                    path = os.path.join(tob_directory, str(row['TOB_name_in_Database:']))

                    if os.path.isfile(path):
                        meta_files += 1
                        df2_series = row.squeeze()
                        quote = str(df2_series.to_string())

                        with open(path, "r", encoding="utf8", errors='ignore') as f:
                            lines = f.readlines()

                        if lines[0] != "*** Meta Data ***\n":
                            added += 1
                            with open(path, "w", encoding="utf8", errors='ignore') as f:
                                f.write("*** Meta Data ***\n")
                                f.write(quote + "\n\n*************\n")
                                f.writelines(lines)
                    else:
                        lost_files += 1

                    # ---------------------------------------------------------
                    # 4. Update progress bar for each row
                    # ---------------------------------------------------------
                    progress["value"] += 1
                    popup.update_idletasks()

            # ---------------------------------------------------------
            # 5. Show summary
            # ---------------------------------------------------------
            tk.Label(popup, text="Done!", font=("Arial", 16), fg="green").pack(pady=10)

            summary_msg = (
                f"Metadata added: {added}\n"
                f"Existing metadata: {meta_files}\n"
                f"Lost files: {lost_files}"
            )
            tk.Label(popup, text=summary_msg, font=("Arial", 12)).pack(pady=10)

        except Exception as e:
            progress.stop()
            tk.Label(popup, text="Something is wrong with your metadata file.",
                     font=("Arial", 16), fg="red").pack(pady=10)
            tk.Label(popup, text=str(e), font=("Arial", 12)).pack()

    threading.Thread(target=worker).start()


# ---------------------------------------------------------
# ADD METADATA ON TOBs
# ---------------------------------------------------------
#directory = "../data/Level0/"
#metadata = '../data/meta_data/0_CTD information_2008-2022_ms_221201.xlsx'

def add_metadata(metadata, directory, start_year, end_year):
    columns = ["Campaign_number:", "Profile_count:", "Profile:", "date:", "Latitude_S_(digital):", "Longitude_E_(digital):",
            "Distance_to_GEF_(m):", "Rope_length_(m):", "Max_depth_(m):", "TOB_name_in_Database:", "Purpose_of_sampling:",
            "pH_Calibration_(7):", "pH_Calibration_(9):", "pH_Calibration_(10):", "pH_Calibration_(4):"]

    no_files = len(os.listdir(directory))
    meta_files = 0
    lost_files = 0
    added = 0

    for year in range(start_year, end_year+1):
        print(year)
        df = pd.read_excel(metadata, sheet_name=str(year), engine='openpyxl', header=None, skiprows=2)
        df = df.iloc[:, :15]
        df.columns = columns
        for index, row in df.iterrows():
            path = os.path.join(directory, str(row['TOB_name_in_Database:']))
            if os.path.isfile(path):
                meta_files += 1
                df2_series = row.squeeze()
                quote = str(df2_series.to_string())
                with open(path, "r", encoding="utf8", errors='ignore') as f:
                    lines = f.readlines()
                if lines[0] != "*** Meta Data ***\n":
                    added += 1
                    with open(path, "w", encoding="utf8", errors='ignore') as f:
                        f.write("*** Meta Data ***")
                        f.write("\n")
                        f.write(quote)
                        f.write("\n")
                        f.write("\n")
                        f.write("*************")
                        f.write("\n")
                        f.writelines(lines)
            else:
                print(path)
                lost_files += 1

    print("Metadata added for {} files and exists for {} out of {} files.".format(added, meta_files, no_files))
    print("{} files have metadata but cannot be located.".format(lost_files))
    print("No metadata is available for {} files.".format(no_files-meta_files))

    return {
    "added_metadata": added,
    "existing_metadata": meta_files,
    "total_tob_files": no_files,
    "lost_files": lost_files,
    "no_metadata_available": no_files - meta_files
    }


COLUMNS = [
    "Campaign_number:", "Profile_count:", "Profile:", "date:",
    "Latitude_S_(digital):", "Longitude_E_(digital):",
    "Distance_to_GEF_(m):", "Rope_length_(m):", "Max_depth_(m):",
    "TOB_name_in_Database:", "Purpose_of_sampling:",
    "pH_Calibration_(7):", "pH_Calibration_(9):",
    "pH_Calibration_(10):", "pH_Calibration_(4):"
]

def create_new_metadata_window():
    win = tk.Toplevel()
    win.title("Create New Metadata")
    win.geometry("900x700")
    win.configure(bg="#CEE5FD")

    tk.Label(
        win,
        text="Create New Metadata Entry",
        font=("Arial", 28, "bold"),
        bg="#CEE5FD"
    ).pack(pady=20)

    form_frame = tk.Frame(win, bg="#CEE5FD")
    form_frame.pack(pady=10)

    entries = {}

    # Create form fields
    for i, col in enumerate(COLUMNS):
        tk.Label(
            form_frame,
            text=col,
            font=("Arial", 14),
            bg="#CEE5FD"
        ).grid(row=i, column=0, sticky="w", pady=5)

        ent = tk.Entry(form_frame, width=40, font=("Arial", 14))
        ent.grid(row=i, column=1, pady=5)
        entries[col] = ent

    # Save button
    def save_new_metadata():
        save_path = filedialog.asksaveasfilename(
            title="Save Metadata Excel File",
            defaultextension=".xlsx",
            filetypes=[("Excel Files", "*.xlsx")]
        )
        if not save_path:
            return

        # Build DataFrame
        data = {col: [entries[col].get()] for col in COLUMNS}
        df = pd.DataFrame(data)

        df.to_excel(save_path, index=False)
        messagebox.showinfo("Saved", "Metadata saved successfully.")

    tk.Button(
        win,
        text="Save Metadata",
        font=("Arial", 18),
        command=save_new_metadata
    ).pack(pady=20)

# ---------------------------------------------------------
# BACK BUTTON (standalone reusable)
# ---------------------------------------------------------
def add_back_button():
    btn_back = tk.Button(
        root,
        text="<<< Back",
        font=("Arial", 16),
        bg="#97B0CA",
        fg="white",
        activebackground="#93C6FC",
        activeforeground="white",
        relief="raised",
        bd=3,
        command=homepage
    )
    btn_back.place(x=20, y=640)   # bottom-left corner

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
        command=lambda: print("TODO: Add new metadata page")
    )
    btn_new.grid(row=1, column=0, padx=20, pady=20)

# ---------------------------------------------------------
# START APPLICATION
# ---------------------------------------------------------
if __name__ == "__main__":
    homepage()
    root.mainloop()

