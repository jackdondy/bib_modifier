import os
import json
import tkinter as tk
from tkinter import filedialog, messagebox
import webbrowser
from lib import process_files


def load_config():
    if os.path.exists("config.json"):
        with open("config.json", "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_config():
    config = {
        "ieee_path": ieee_var.get(),
        "word_abbr_path": word_abbr_var.get(),
        "aux_path": aux_var.get(),
        "bib_path": bib_var.get(),
        "new_bib_path": new_bib_var.get(),
        "skip_date_check": skip_var.get() == "True",
        "es_cmd_path": es_var.get() if skip_var.get() == "False" and es_var.get() != "System Default" else None
    }
    with open("config.json", "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)
    messagebox.showinfo("Save Successful", "Configuration saved!")
    return config

def browse_file(var):
    filepath = filedialog.askopenfilename()
    if filepath:
        var.set(filepath)

def on_skip_change():
    if skip_var.get() == "False":
        es_entry.config(state=tk.NORMAL)
        es_button.config(state=tk.NORMAL)
        es_default_button.config(state=tk.NORMAL)
    else:
        es_var.set("")
        es_entry.config(state=tk.DISABLED)
        es_button.config(state=tk.DISABLED)
        es_default_button.config(state=tk.DISABLED)

def use_default_es_path():
    es_var.set("System Default")

def run_program():
    config = save_config()
    messagebox.showinfo("Processing", "Processing files with the given configuration...")

    process_files(aux_path=config['aux_path'],
                  ieee_full_bib_path=config['ieee_path'],
                  word_addr_csv_path=config['word_abbr_path'],
                  bib_path=config['bib_path'],
                  skip_date_check=config['skip_date_check'],
                  es_cmd_path=config['es_cmd_path'],
                  new_bib_path=config['new_bib_path'],
                  )


config = load_config()

root = tk.Tk()
root.title("Configuration Tool")
root.resizable(True, True)

ieee_var = tk.StringVar(value=config.get("ieee_path", ""))
word_abbr_var = tk.StringVar(value=config.get("word_abbr_path", ""))
aux_var = tk.StringVar(value=config.get("aux_path", ""))
bib_var = tk.StringVar(value=config.get("bib_path", ""))
new_bib_var = tk.StringVar(value=config.get("new_bib_path", ""))
skip_var = tk.StringVar(value=str(config.get("skip_date_check", "False")))
es_var = tk.StringVar(value=config.get("es_cmd_path", ""))

def create_file_input(label, var, url=None):  # 新增 url 参数
    frame = tk.Frame(root)
    # 创建标签并配置样式和事件
    if url:
        lbl = tk.Label(
            frame,
            text=label,
            width=15,
            fg="blue",  # 设置蓝色（仅当有 URL 时）
            cursor="hand2"  # 手型光标（仅当有 URL 时）
        )
        lbl.bind("<Button-1>", lambda e: webbrowser.open(url))  # 绑定点击事件
    else:
        lbl = tk.Label(
            frame,
            text=label,
            width=15,
            fg="black",
            cursor=""
        )
    lbl.pack(side=tk.LEFT)
    # 原有 Entry 和 Button 代码保持不变
    entry = tk.Entry(frame, textvariable=var)
    entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
    tk.Button(frame, text="Browse", command=lambda: browse_file(var)).pack(side=tk.LEFT)
    frame.pack(pady=2, padx=5, fill=tk.X)
    return frame


create_file_input("IEEEfull.bib Path", ieee_var, url="https://ctan.org/tex-archive/macros/latex/contrib/IEEEtran/bibtex")
create_file_input("ITWA_XXX.csv Path", word_abbr_var, url="https://www.issn.org/wp-content/uploads/2024/02/ltwa_current.csv")
create_file_input(".aux Path", aux_var)
create_file_input(".bib Path", bib_var)
create_file_input("New .bib Path", new_bib_var)

frame = tk.Frame(root)
tk.Label(frame, text="Skip Date Check", width=15).pack(side=tk.LEFT)
skip_true = tk.Radiobutton(frame, text="True", variable=skip_var, value="True", command=on_skip_change)
skip_false = tk.Radiobutton(frame, text="False", variable=skip_var, value="False", command=on_skip_change)
skip_true.pack(side=tk.LEFT)
skip_false.pack(side=tk.LEFT)
frame.pack(pady=2, padx=5, fill=tk.X)

es_frame = tk.Frame(root)
tk.Label(es_frame, text="ES Cmd Path", width=15).pack(side=tk.LEFT)
es_entry = tk.Entry(es_frame, textvariable=es_var)
es_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
es_button = tk.Button(es_frame, text="Browse", command=lambda: browse_file(es_var))
es_button.pack(side=tk.LEFT)
es_default_button = tk.Button(es_frame, text="Use Default", command=use_default_es_path)
es_default_button.pack(side=tk.LEFT)
es_frame.pack(pady=2, padx=5, fill=tk.X)

on_skip_change()

btn_frame = tk.Frame(root)
tk.Button(btn_frame, text="Save Config", command=save_config).pack(side=tk.LEFT, padx=5)
tk.Button(btn_frame, text="OK", command=run_program).pack(side=tk.RIGHT, padx=5)
btn_frame.pack(pady=10)

root.mainloop()
