import pandas as pd
import customtkinter as ctk
from tkinter import filedialog, messagebox, ttk
import random, re, threading
from faker import Faker

fake = Faker()


def mask_structured(value, column_name, mode="random"):
    if pd.isnull(value):
        return value
    col = column_name.lower()
    if mode == "label":
        if "name" in col: return "[NAME]"
        elif "email" in col: return "[EMAIL]"
        elif "phone" in col or "contact" in col: return "[PHONE]"
        elif "address" in col or "location" in col: return "[ADDRESS]"
        elif "company" in col or "organization" in col: return "[COMPANY]"
        elif "date" in col or "dob" in col: return "[DATE]"
        elif "salary" in col or "income" in col: return "[SALARY]"
        return "[DATA]"

   
    if "name" in col:
        return fake.name()
    elif "email" in col:
        return fake.email()
    elif "phone" in col or "contact" in col:
        return fake.numerify("###-###-####")
    elif "address" in col or "location" in col:
        return fake.address().replace("\n", ", ")
    elif "company" in col or "organization" in col:
        return fake.company()
    elif "date" in col or "dob" in col:
        return fake.date_of_birth(minimum_age=22, maximum_age=60).strftime("%Y-%m-%d")
    elif "salary" in col or "income" in col:
        return random.randint(40000, 120000)
    return value


def mask_unstructured(text, mode="random"):
    if pd.isnull(text):
        return text
    text = str(text)
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    phone_pattern = r'(\+?\d[\d -]{8,}\d)'
    name_pattern = r'\b([A-Z][a-z]+ [A-Z][a-z]+)\b'

    if mode == "label":
        text = re.sub(email_pattern, "[EMAIL]", text)
        text = re.sub(phone_pattern, "[PHONE]", text)
        text = re.sub(name_pattern, "[NAME]", text)
    else:
        text = re.sub(email_pattern, fake.email(), text)
        text = re.sub(phone_pattern, fake.phone_number(), text)
        text = re.sub(name_pattern, fake.name(), text)
    return text

def anonymize_df(df, sensitive_columns, mode, progress_callback=None):
    anonymized_df = df.copy()
    total = len(sensitive_columns)
    for i, col in enumerate(sensitive_columns):
        anonymized_df[col] = anonymized_df[col].apply(lambda x: mask_structured(x, col, mode))
       
        if anonymized_df[col].dtype == object and not any(k in col.lower() for k in ["email","phone","contact","salary","dob","date","name"]):
            anonymized_df[col] = anonymized_df[col].apply(lambda x: mask_unstructured(x, mode))
        if progress_callback:
            progress_callback((i + 1) / total)
    return anonymized_df


# ------------------ GUI ------------------
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

root = ctk.CTk()
root.title("Anonify - AI Data Anonymizer")
root.geometry("1100x700")

sidebar = ctk.CTkFrame(root, width=250, corner_radius=0, fg_color="#2C3E50")
sidebar.pack(side="left", fill="y")

ctk.CTkLabel(sidebar, text="Anonify", font=ctk.CTkFont(size=30, weight="bold"), text_color="#1ABC9C").pack(pady=(40, 10))
ctk.CTkLabel(sidebar, text=" AI Data Anonymizer", font=ctk.CTkFont(size=14), text_color="#BDC3C7").pack(pady=(0, 30))

file_frame = ctk.CTkFrame(sidebar, fg_color="#34495E", corner_radius=8)
file_frame.pack(padx=20, pady=(10, 20), fill="x")

ctk.CTkLabel(file_frame, text="Select File:", anchor="w").pack(padx=10, pady=(8, 2), fill="x")
entry_file = ctk.CTkEntry(file_frame, width=200)
entry_file.pack(padx=10, pady=5)

def select_file():
    file_path = filedialog.askopenfilename(title="Select Excel/CSV File",
                                           filetypes=[("Excel/CSV Files", "*.xlsx *.xls *.csv")])
    if file_path:
        entry_file.delete(0, ctk.END)
        entry_file.insert(0, file_path)

ctk.CTkButton(file_frame, text="Browse", command=select_file, fg_color="#3498DB").pack(padx=10, pady=(5, 10))

ctk.CTkLabel(sidebar, text="Anonymization Mode:", text_color="#ECF0F1").pack(padx=20, pady=(10, 0), anchor="w")
mode_var = ctk.StringVar(value="random")
ctk.CTkOptionMenu(sidebar, variable=mode_var, values=["random", "label"]).pack(padx=20, pady=(5, 20), fill="x")

def load_columns():
    file_path = entry_file.get()
    if not file_path:
        messagebox.showerror("Error", "Please select a file first.")
        return
    try:
        df = pd.read_csv(file_path) if file_path.endswith(".csv") else pd.read_excel(file_path)
    except Exception as e:
        messagebox.showerror("Error", str(e))
        return

    for widget in frame_columns.winfo_children():
        if isinstance(widget, ctk.CTkCheckBox):
            widget.destroy()

    global column_vars
    column_vars = {}
    for col in df.columns:
        var = ctk.BooleanVar()
        chk = ctk.CTkCheckBox(frame_columns, text=col, variable=var)
        chk.pack(anchor="w", pady=2)
        column_vars[col] = var

ctk.CTkButton(sidebar, text="Load Columns", command=load_columns, fg_color="#2980B9").pack(pady=(10, 10), padx=20, fill="x")

ctk.CTkButton(sidebar, text="Anonymize Data", command=lambda: start_anonymization(), fg_color="#1ABC9C").pack(padx=20, pady=(10, 5), fill="x")

progress = ctk.CTkProgressBar(sidebar, width=180, progress_color="#27AE60")
progress.pack_forget()

ctk.CTkButton(sidebar, text="Save Anonymized File", command=lambda: save_file(), fg_color="#27AE60").pack(padx=20, pady=(0, 20), fill="x")

# Main
main_content = ctk.CTkFrame(root, corner_radius=0, fg_color="#ECF0F1")
main_content.pack(side="left", fill="both", expand=True)

frame_columns = ctk.CTkScrollableFrame(main_content, height=120, label_text="Columns to Anonymize",
                                       label_font=ctk.CTkFont(size=16, weight="bold"))
frame_columns.pack(fill="x", padx=20, pady=(20, 10))

preview_frame = ctk.CTkFrame(main_content)
preview_frame.pack(fill="both", expand=True, padx=20, pady=20)

tree = ttk.Treeview(preview_frame)
tree.pack(fill="both", expand=True)

def show_preview(df):
    tree.delete(*tree.get_children())
    tree["columns"] = list(df.columns)
    tree["show"] = "headings"
    for col in df.columns:
        tree.heading(col, text=col)
        tree.column(col, anchor="center", width=150)
    for _, row in df.iterrows():
        tree.insert("", "end", values=list(row))

# ------------------ Anonymization ------------------
def start_anonymization():
    threading.Thread(target=anonymize_file, daemon=True).start()

def anonymize_file():
    progress.pack(pady=(15, 20), padx=30)
    progress.set(0)
    root.update_idletasks()

    file_path = entry_file.get()
    if not file_path:
        messagebox.showerror("Error", "Select a file first.")
        progress.pack_forget()
        return

    try:
        df = pd.read_csv(file_path) if file_path.endswith(".csv") else pd.read_excel(file_path)
    except Exception as e:
        messagebox.showerror("Error", str(e))
        progress.pack_forget()
        return

    sensitive_columns = [col for col, var in column_vars.items() if var.get()]
    if not sensitive_columns:
        sensitive_columns = [col for col in df.columns if any(x in col.lower() for x in ["name","email","phone","contact","dob","salary","address","company"])]

    anonymized_df = anonymize_df(df, sensitive_columns, mode_var.get(), progress_callback=lambda v: progress.set(v))
    show_preview(anonymized_df.head(50))
    progress.set(1.0)

def save_file():
    items = tree.get_children()
    if not items:
        messagebox.showinfo("Info", "No data to save. Please anonymize first.")
        return
    data = [tree.item(item)['values'] for item in items]
    df_to_save = pd.DataFrame(data, columns=tree["columns"])
    save_path = filedialog.asksaveasfilename(defaultextension=".xlsx",
                                             filetypes=[("Excel Files", "*.xlsx"), ("CSV Files", "*.csv")],
                                             title="Save File")
    if save_path:
        if save_path.endswith(".csv"):
            df_to_save.to_csv(save_path, index=False)
        else:
            df_to_save.to_excel(save_path, index=False)
        messagebox.showinfo("Success", f"File saved successfully:\n{save_path}")

root.mainloop()
