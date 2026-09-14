# -*- coding: utf-8 -*-
"""
Created on Tue Mar 29 11:00:10 2022

@author: thomitob
"""

import os
import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox

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

    for year in range(start_year, end_year):
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


def metadata_gui():
    """GUI interface for adding metadata to TOB files."""

    def select_metadata():
        path = filedialog.askopenfilename(
            title="Select Metadata Excel File",
            filetypes=[("Excel Files", "*.xlsx *.xls")]
        )
        metadata_entry.delete(0, tk.END)
        metadata_entry.insert(0, path)

    def select_directory():
        path = filedialog.askdirectory(title="Select TOB Directory")
        directory_entry.delete(0, tk.END)
        directory_entry.insert(0, path)

    def run_processing():
        metadata_path = metadata_entry.get()
        tob_directory = directory_entry.get()
        try:
            start_year = int(start_year_entry.get())
            end_year = int(end_year_entry.get())
        except ValueError:
            messagebox.showerror("Error", "Years must be integers")
            return

        try:
            summary = add_metadata(metadata_path, tob_directory, start_year, end_year)
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return

        msg = (
            f"Metadata added: {summary['added_metadata']}\n"
            f"Existing metadata: {summary['existing_metadata']}\n"
            f"Total TOB files: {summary['total_tob_files']}\n"
            f"Lost files: {summary['lost_files']}\n"
            f"No metadata available: {summary['no_metadata_available']}"
        )
        messagebox.showinfo("Processing Complete", msg)

    # --- GUI WINDOW ---
    root = tk.Tk()
    root.title("Lake Kivu Metadata Inserter")

    tk.Label(root, text="Metadata Excel File:").grid(row=0, column=0, sticky="w")
    metadata_entry = tk.Entry(root, width=50)
    metadata_entry.grid(row=0, column=1)
    tk.Button(root, text="Browse", command=select_metadata).grid(row=0, column=2)

    tk.Label(root, text="TOB Directory:").grid(row=1, column=0, sticky="w")
    directory_entry = tk.Entry(root, width=50)
    directory_entry.grid(row=1, column=1)
    tk.Button(root, text="Browse", command=select_directory).grid(row=1, column=2)

    tk.Label(root, text="Start Year:").grid(row=2, column=0, sticky="w")
    start_year_entry = tk.Entry(root, width=10)
    start_year_entry.grid(row=2, column=1, sticky="w")

    tk.Label(root, text="End Year:").grid(row=3, column=0, sticky="w")
    end_year_entry = tk.Entry(root, width=10)
    end_year_entry.grid(row=3, column=1, sticky="w")

    tk.Button(root, text="Run Metadata Processing", command=run_processing).grid(row=4, column=1, pady=10)

    root.mainloop()


def lake_kivu_homepage():
    root = tk.Tk()
    root.title("Lake Kivu CTD Database")
    root.geometry("1200x700")
    root.configure(bg="#4A90E2")   # soft blue

    # Title
    title = tk.Label(
        root,
        text="Lake Kivu CTD Database",
        font=("Arial", 36, "bold"),
        bg="#4A90E2",
        fg="white"
    )
    title.pack(pady=20)

    subtitle = tk.Label(
        root,
        text="in-situ observations",
        font=("Arial", 20),
        bg="#4A90E2",
        fg="white"
    )
    subtitle.pack(pady=5)

    # Buttons frame
    frame = tk.Frame(root, bg="#4A90E2")
    frame.pack(pady=80)

    # Button 1: Load existing metadata
    btn_load = tk.Button(
        frame,
        text="Load and add existing metadata",
        font=("Arial", 20),
        width=30,
        command=metadata_gui
    )
    btn_load.grid(row=0, column=0, padx=20, pady=20)

    # Button 2: Create new metadata
    btn_new = tk.Button(
        frame,
        text="Create new metadata",
        font=("Arial", 20),
        width=30,
        command=create_new_metadata_window
    )
    btn_new.grid(row=1, column=0, padx=20, pady=20)

    root.mainloop()


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

if __name__ == "__main__":
    lake_kivu_homepage()

