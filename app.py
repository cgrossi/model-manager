import os
import shutil
import threading
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, Listbox, END, EXTENDED, LabelFrame, Scrollbar, StringVar, Label

# Globals
in_use_folder = None
not_in_use_folder = None
model_extensions = [".safetensors", ".ckpt", ".gguf"]

# State
use_all_files = []
unused_all_files = []
selected_use_files = set()
selected_unused_files = set()

# --- GUI Setup ---
root = tk.Tk()
root.title("ComfyUI Model Manager")
root.geometry("1000x720")

loras_use_listbox = None
loras_unused_listbox = None

search_var_use = StringVar()
search_var_unused = StringVar()

# --- Functions ---
def choose_in_use_folder():
    global in_use_folder
    path = filedialog.askdirectory(title="Select 'In Use' Folder")
    if path:
        in_use_folder = Path(path)
        threaded_refresh()

def choose_not_in_use_folder():
    global not_in_use_folder
    path = filedialog.askdirectory(title="Select 'Not In Use' Folder")
    if path:
        not_in_use_folder = Path(path)
        threaded_refresh()

def is_model_file(file):
    return file.suffix.lower() in model_extensions

def get_selected_items(listbox):
    return [listbox.get(i) for i in listbox.curselection()]

def filter_and_display(listbox, all_files, search_text, selected_set):
    listbox.delete(0, END)
    filtered_items = []
    for item in all_files:
        if search_text.lower() in str(item).lower():
            filtered_items.append(str(item))
            listbox.insert(END, item)
    for i, item in enumerate(filtered_items):
        if item in selected_set:
            listbox.selection_set(i)

def threaded_refresh():
    threading.Thread(target=refresh_lists, daemon=True).start()

def refresh_lists():
    global use_all_files, unused_all_files
    if not in_use_folder or not not_in_use_folder:
        return

    loras_use_listbox.delete(0, END)
    loras_use_listbox.insert(END, "Loading...")
    loras_unused_listbox.delete(0, END)
    loras_unused_listbox.insert(END, "Loading...")

    use_all_files = [file.relative_to(in_use_folder) for file in in_use_folder.rglob("*") if file.is_file() and is_model_file(file)]
    unused_all_files = [file.relative_to(not_in_use_folder) for file in not_in_use_folder.rglob("*") if file.is_file() and is_model_file(file)]

    root.after(0, lambda: update_search_use())
    root.after(0, lambda: update_search_unused())

def move_file_smart(src_root, dst_root, relative_path):
    src = src_root / relative_path
    dst = dst_root / relative_path
    dst.parent.mkdir(parents=True, exist_ok=True)

    if src.drive == dst.drive:
        shutil.move(str(src), str(dst))
    else:
        shutil.copy2(str(src), str(dst))
        os.remove(str(src))

def move_to_unused():
    global selected_use_files
    selected_use_files.update(get_selected_items(loras_use_listbox))
    if selected_use_files and in_use_folder and not_in_use_folder:
        for rel_path_str in list(selected_use_files):
            move_file_smart(in_use_folder, not_in_use_folder, Path(rel_path_str))
        selected_use_files.clear()
        threaded_refresh()

def move_to_use():
    global selected_unused_files
    selected_unused_files.update(get_selected_items(loras_unused_listbox))
    if selected_unused_files and in_use_folder and not_in_use_folder:
        for rel_path_str in list(selected_unused_files):
            move_file_smart(not_in_use_folder, in_use_folder, Path(rel_path_str))
        selected_unused_files.clear()
        threaded_refresh()

def update_search_use(*args):
    selected_use_files.update(get_selected_items(loras_use_listbox))
    filter_and_display(loras_use_listbox, use_all_files, search_var_use.get(), selected_use_files)

def update_search_unused(*args):
    selected_unused_files.update(get_selected_items(loras_unused_listbox))
    filter_and_display(loras_unused_listbox, unused_all_files, search_var_unused.get(), selected_unused_files)

# --- Layout ---
btn_frame = tk.Frame(root)
btn_frame.pack(pady=10)

choose_in_use_btn = tk.Button(btn_frame, text="Select In-Use Folder", command=choose_in_use_folder)
choose_in_use_btn.pack(side="left", padx=10)

choose_not_in_use_btn = tk.Button(btn_frame, text="Select Not-In-Use Folder", command=choose_not_in_use_folder)
choose_not_in_use_btn.pack(side="left", padx=10)

# Instructions
instructions = Label(root, text=(
    "How to Use:\n"
    "- Select your 'In Use' and 'Not In Use' folders above\n"
    "- Browse or search through your models\n"
    "- Select one or more models (hold Ctrl or Shift)\n"
    "- Use the arrows to move models between folders\n"
    "- Folder structure is preserved during moves\n"
    "- Selections persist across searches and are always moved"
), justify="left")
instructions.pack(pady=(5, 0))

main_frame = tk.Frame(root)
main_frame.pack(fill="both", expand=True, padx=20, pady=10)

# Left - Use
lf_use = LabelFrame(main_frame, text="Models in USE")
lf_use.pack(side="left", fill="both", expand=True, padx=10)

search_entry_use = tk.Entry(lf_use, textvariable=search_var_use)
search_entry_use.pack(fill="x", padx=5)
search_var_use.trace("w", update_search_use)

use_scroll = Scrollbar(lf_use)
use_scroll.pack(side="right", fill="y")
loras_use_listbox = Listbox(lf_use, selectmode=EXTENDED, yscrollcommand=use_scroll.set)
loras_use_listbox.pack(fill="both", expand=True, padx=5, pady=5)
use_scroll.config(command=loras_use_listbox.yview)

# Middle - Buttons
action_frame = tk.Frame(main_frame)
action_frame.pack(side="left", fill="y")

btn_to_unused = tk.Button(action_frame, text="→ Move to Not In Use →", command=move_to_unused)
btn_to_unused.pack(pady=10)

btn_to_use = tk.Button(action_frame, text="← Move to Use ←", command=move_to_use)
btn_to_use.pack(pady=10)

# Right - Not in Use
lf_unused = LabelFrame(main_frame, text="Models NOT in Use")
lf_unused.pack(side="left", fill="both", expand=True, padx=10)

search_entry_unused = tk.Entry(lf_unused, textvariable=search_var_unused)
search_entry_unused.pack(fill="x", padx=5)
search_var_unused.trace("w", update_search_unused)

unused_scroll = Scrollbar(lf_unused)
unused_scroll.pack(side="right", fill="y")
loras_unused_listbox = Listbox(lf_unused, selectmode=EXTENDED, yscrollcommand=unused_scroll.set)
loras_unused_listbox.pack(fill="both", expand=True, padx=5, pady=5)
unused_scroll.config(command=loras_unused_listbox.yview)

# --- Start ---
root.mainloop()