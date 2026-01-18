import storage
import tkinter as tk
from tkinter import ttk
import os, sys

def resource_path(relative_path):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), relative_path)

# =========================
# THEME
# =========================
THEME = {
    "bg": "#0F1115",
    "panel": "#0F1115",
    "card": "#161A22",
    "border": "#242A36",
    "text": "#EAF0FF",
    "muted": "#AAB3C5",
    "accent": "#6A5CFF",
    "danger": "#FF4D6D",
    "success": "#22C55E",
    "warn": "#F59E0B",
    "field": "#0B0E14",
    "btn": "#1E2431",
}

FONT_TITLE = ("Segoe UI", 20, "bold")
FONT_SUB = ("Segoe UI", 10)
FONT_H2 = ("Segoe UI", 12, "bold")
FONT_BODY = ("Segoe UI", 11)

# =========================
# APP
# =========================
app = tk.Tk()
app.title("N-Notas v1.2")
app.state("zoomed")
app.configure(bg=THEME["bg"])

try:
    icon = tk.PhotoImage(file=resource_path("icon.png"))
    app.iconphoto(True, icon)
except Exception:
    pass

app.grid_rowconfigure(0, weight=1)
app.grid_columnconfigure(0, weight=1)

panel = tk.Frame(app, bg=THEME["panel"])
panel.grid(row=0, column=0, sticky="nsew", padx=24, pady=24)
panel.grid_columnconfigure(0, weight=1)
panel.grid_columnconfigure(1, weight=2)
panel.grid_rowconfigure(0, weight=0)
panel.grid_rowconfigure(1, weight=0)
panel.grid_rowconfigure(2, weight=1)
panel.grid_rowconfigure(3, weight=0)

def make_card(parent, title=None):
    card = tk.Frame(parent, bg=THEME["card"], highlightthickness=1, highlightbackground=THEME["border"])
    if title:
        hdr = tk.Frame(card, bg=THEME["card"])
        hdr.pack(fill="x", padx=16, pady=(14, 6))
        tk.Label(hdr, text=title, bg=THEME["card"], fg=THEME["text"], font=FONT_H2).pack(anchor="w")
    body = tk.Frame(card, bg=THEME["card"])
    body.pack(fill="both", expand=True, padx=16, pady=(0, 14))
    return card, body

def set_status(msg, color=None):
    status_label.config(text=msg or "", fg=color or THEME["muted"])

# =========================
# State vars
# =========================
storage.load_data()  # fuerza creación/migración si hace falta

ramo_var = tk.StringVar(value=storage.get_ramo_activo())
nivel_var = tk.StringVar(value=storage.get_nivel())

# =========================
# Refresh helpers (AUTO)
# =========================
def refresh_ramos_dropdown(keep_current=True):
    ramos = storage.get_ramos()
    if not ramos:
        ramos = ["Matemática"]
    current = ramo_var.get()
    if keep_current and current in ramos:
        pass
    else:
        ramo_var.set(storage.get_ramo_activo() if storage.get_ramo_activo() in ramos else ramos[0])
        storage.set_ramo_activo(ramo_var.get())

    ramo_combo["values"] = ramos

def refresh_nivel_ui():
    enabled = storage.ponderacion_habilitada()
    if enabled:
        peso_entry.configure(state="normal")
        peso_label.configure(text="Peso (%) opcional (solo Uni/Post)")
        peso_hint.configure(text="Ej: 50 25 25 (si usas peso, deben sumar 100%)")
    else:
        peso_entry.configure(state="disabled")
        peso_entry.delete(0, tk.END)
        peso_label.configure(text="Peso (%) (bloqueado en Escolar)")
        peso_hint.configure(text="Escolar no usa ponderaciones (para no enredar).")

def refresh_list():
    listbox.delete(0, tk.END)
    evs = storage.get_evaluaciones(ramo_var.get())
    for ev in evs:
        if "peso" in ev:
            listbox.insert(tk.END, f'{ev["nota"]:.2f}   —   {ev["peso"]:.2f}%')
        else:
            listbox.insert(tk.END, f'{ev["nota"]:.2f}')

def refresh_summary():
    # Promedio ramo (auto)
    prom_r, estado_r = storage.promedio_ramo(ramo_var.get())

    if prom_r is None:
        prom_ramo_big.config(text="—")
        chip_ramo.config(text="SIN DATOS", fg=THEME["muted"])
    else:
        prom_ramo_big.config(text=f"{prom_r:.2f}")
        chip_ramo.config(
            text=("APROBANDO" if prom_r >= 4.0 else "REPROBANDO"),
            fg=(THEME["success"] if prom_r >= 4.0 else THEME["danger"])
        )

    # Promedio global (auto)
    prom_g, estado_g = storage.promedio_global()
    if prom_g is None:
        prom_global_big.config(text="—")
        chip_global.config(text="SIN DATOS", fg=THEME["muted"])
    else:
        prom_global_big.config(text=f"{prom_g:.2f}")
        chip_global.config(
            text=("APROBANDO" if prom_g >= 4.0 else "REPROBANDO"),
            fg=(THEME["success"] if prom_g >= 4.0 else THEME["danger"])
        )

    count_label.config(text=f'{len(storage.get_evaluaciones(ramo_var.get()))} evaluación(es)')

def refresh_all():
    refresh_ramos_dropdown(keep_current=True)
    refresh_nivel_ui()
    refresh_list()
    refresh_summary()

# =========================
# Events
# =========================
def on_change_ramo(_=None):
    storage.set_ramo_activo(ramo_var.get())
    refresh_all()
    set_status(f"Ramo activo: {ramo_var.get()}", THEME["muted"])

def on_change_nivel(_=None):
    storage.set_nivel(nivel_var.get())
    refresh_all()
    set_status(f"Nivel: {nivel_var.get()}", THEME["muted"])

def agregar_evaluacion():
    nota = storage.parse_nota(nota_entry.get())
    if nota is None:
        set_status("Nota inválida (1.0 a 7.0).", THEME["danger"])
        nota_entry.delete(0, tk.END)
        nota_entry.focus_set()
        return

    peso = None
    if storage.ponderacion_habilitada():
        txt = (peso_entry.get() or "").strip()
        if txt:
            peso = storage.parse_peso(txt)
            if peso is None:
                set_status("Peso inválido (ej: 50).", THEME["danger"])
                peso_entry.focus_set()
                return

    ok, msg = storage.add_evaluacion(nota, peso=peso, ramo=ramo_var.get())
    if not ok:
        set_status(msg, THEME["danger"])
        return

    nota_entry.delete(0, tk.END)
    peso_entry.delete(0, tk.END)
    nota_entry.focus_set()
    refresh_all()
    set_status("Evaluación agregada.", THEME["success"])

def borrar_seleccion():
    sel = listbox.curselection()
    if not sel:
        set_status("Selecciona una evaluación para borrar.", THEME["warn"])
        return
    idx = sel[0]
    ok, msg = storage.delete_evaluacion(idx, ramo=ramo_var.get())
    refresh_all()
    set_status(msg, THEME["muted"] if ok else THEME["danger"])

def borrar_ultima():
    evs = storage.get_evaluaciones(ramo_var.get())
    if not evs:
        set_status("No hay evaluaciones.", THEME["warn"])
        return
    ok, msg = storage.delete_evaluacion(len(evs)-1, ramo=ramo_var.get())
    refresh_all()
    set_status(msg, THEME["muted"] if ok else THEME["danger"])

def limpiar_ramo():
    storage.clear_evaluaciones(ramo_var.get())
    refresh_all()
    set_status("Ramo limpio.", THEME["muted"])

# Ramos CRUD
def add_ramo_ui():
    name = (ramo_name_entry.get() or "").strip()
    if not name:
        set_status("Escribe un nombre de ramo.", THEME["warn"])
        return
    ok, msg = storage.add_ramo(name)
    if ok:
        storage.set_ramo_activo(name)
        ramo_var.set(name)
    ramo_name_entry.delete(0, tk.END)
    refresh_all()
    set_status(msg, THEME["success"] if ok else THEME["danger"])

def rename_ramo_ui():
    old = ramo_var.get()
    new = (ramo_name_entry.get() or "").strip()
    if not new:
        set_status("Escribe el nuevo nombre del ramo.", THEME["warn"])
        return
    ok, msg = storage.rename_ramo(old, new)
    if ok:
        ramo_var.set(new)
    ramo_name_entry.delete(0, tk.END)
    refresh_all()
    set_status(msg, THEME["success"] if ok else THEME["danger"])

def delete_ramo_ui():
    r = ramo_var.get()
    ok, msg = storage.delete_ramo(r)
    refresh_all()
    set_status(msg, THEME["muted"] if ok else THEME["danger"])

# =========================
# UI — LEFT
# =========================
card_header, header_body = make_card(panel)
card_header.grid(row=0, column=0, sticky="ew", padx=(0, 16), pady=(0, 16))

tk.Label(header_body, text="N-Notas", bg=THEME["card"], fg=THEME["text"], font=FONT_TITLE).pack(anchor="w")
tk.Label(
    header_body,
    text="v1.2 ",
    bg=THEME["card"], fg=THEME["muted"], font=FONT_SUB
).pack(anchor="w", pady=(2, 12))

# Selectors
selectors = tk.Frame(header_body, bg=THEME["card"])
selectors.pack(fill="x")

tk.Label(selectors, text="Ramo", bg=THEME["card"], fg=THEME["muted"], font=FONT_SUB).grid(row=0, column=0, sticky="w")
ramo_combo = ttk.Combobox(selectors, textvariable=ramo_var, state="readonly", width=20)
ramo_combo.grid(row=1, column=0, sticky="w", padx=(0, 16))
ramo_combo.bind("<<ComboboxSelected>>", on_change_ramo)

tk.Label(selectors, text="Nivel", bg=THEME["card"], fg=THEME["muted"], font=FONT_SUB).grid(row=0, column=1, sticky="w")
nivel_combo = ttk.Combobox(selectors, textvariable=nivel_var, state="readonly", width=20, values=["Escolar", "Universidad", "Postgrado"])
nivel_combo.grid(row=1, column=1, sticky="w")
nivel_combo.bind("<<ComboboxSelected>>", on_change_nivel)

# Summary row
sumrow = tk.Frame(header_body, bg=THEME["card"])
sumrow.pack(fill="x", pady=(14, 0))

# Ramo
ramo_box = tk.Frame(sumrow, bg=THEME["card"])
ramo_box.pack(side="left", padx=(0, 24))

tk.Label(ramo_box, text="Promedio del ramo", bg=THEME["card"], fg=THEME["muted"], font=FONT_SUB).pack(anchor="w")
prom_ramo_big = tk.Label(ramo_box, text="—", bg=THEME["card"], fg=THEME["text"], font=("Segoe UI", 28, "bold"))
prom_ramo_big.pack(anchor="w")
chip_ramo = tk.Label(ramo_box, text="SIN DATOS", bg=THEME["card"], fg=THEME["muted"], font=("Segoe UI", 10, "bold"))
chip_ramo.pack(anchor="w")

# Global
global_box = tk.Frame(sumrow, bg=THEME["card"])
global_box.pack(side="left")

tk.Label(global_box, text="Promedio global", bg=THEME["card"], fg=THEME["muted"], font=FONT_SUB).pack(anchor="w")
prom_global_big = tk.Label(global_box, text="—", bg=THEME["card"], fg=THEME["text"], font=("Segoe UI", 28, "bold"))
prom_global_big.pack(anchor="w")
chip_global = tk.Label(global_box, text="SIN DATOS", bg=THEME["card"], fg=THEME["muted"], font=("Segoe UI", 10, "bold"))
chip_global.pack(anchor="w")

count_label = tk.Label(header_body, text="0 evaluación(es)", bg=THEME["card"], fg=THEME["muted"], font=FONT_SUB)
count_label.pack(anchor="w", pady=(10, 0))

# Input card
card_input, input_body = make_card(panel, "Agregar evaluación (auto-calcula)")
card_input.grid(row=1, column=0, sticky="ew", padx=(0, 16), pady=(0, 16))

tk.Label(input_body, text="Nota (1.0 a 7.0)", bg=THEME["card"], fg=THEME["muted"], font=FONT_SUB).pack(anchor="w")
nota_entry = tk.Entry(
    input_body, bg=THEME["field"], fg=THEME["text"], insertbackground=THEME["text"],
    relief="flat", highlightthickness=1, highlightbackground=THEME["border"], highlightcolor=THEME["accent"],
    font=("Segoe UI", 12),
)
nota_entry.pack(fill="x", pady=(6, 10))

peso_label = tk.Label(input_body, text="Peso (%)", bg=THEME["card"], fg=THEME["muted"], font=FONT_SUB)
peso_label.pack(anchor="w")
peso_entry = tk.Entry(
    input_body, bg=THEME["field"], fg=THEME["text"], insertbackground=THEME["text"],
    relief="flat", highlightthickness=1, highlightbackground=THEME["border"], highlightcolor=THEME["accent"],
    font=("Segoe UI", 12),
)
peso_entry.pack(fill="x", pady=(6, 6))

peso_hint = tk.Label(input_body, text="", bg=THEME["card"], fg=THEME["muted"], font=FONT_SUB)
peso_hint.pack(anchor="w", pady=(0, 10))

btn_add = tk.Button(
    input_body, text="Agregar", command=agregar_evaluacion,
    bg=THEME["accent"], fg="white", activebackground=THEME["accent"], activeforeground="white",
    relief="flat", padx=14, pady=10, font=("Segoe UI", 11, "bold"),
)
btn_add.pack(fill="x")

nota_entry.bind("<Return>", lambda e: agregar_evaluacion())

# Actions card
card_actions, actions_body = make_card(panel, "Acciones")
card_actions.grid(row=2, column=0, sticky="nsew", padx=(0, 16), pady=(0, 16))

tk.Button(
    actions_body, text="Borrar seleccionada", command=borrar_seleccion,
    bg=THEME["btn"], fg=THEME["text"], activebackground=THEME["btn"], activeforeground=THEME["text"],
    relief="flat", padx=12, pady=10, font=("Segoe UI", 10, "bold"),
).pack(fill="x", pady=(0, 10))

tk.Button(
    actions_body, text="Borrar última", command=borrar_ultima,
    bg=THEME["btn"], fg=THEME["text"], activebackground=THEME["btn"], activeforeground=THEME["text"],
    relief="flat", padx=12, pady=10, font=("Segoe UI", 10, "bold"),
).pack(fill="x", pady=(0, 10))

tk.Button(
    actions_body, text="Limpiar ramo", command=limpiar_ramo,
    bg=THEME["danger"], fg="white", activebackground=THEME["danger"], activeforeground="white",
    relief="flat", padx=12, pady=10, font=("Segoe UI", 10, "bold"),
).pack(fill="x")

# Ramos card
card_ramos, ramos_body = make_card(panel, "Ramos (editar)")
card_ramos.grid(row=3, column=0, sticky="ew", padx=(0, 16), pady=(0, 0))

tk.Label(ramos_body, text="Nombre (agregar/renombrar)", bg=THEME["card"], fg=THEME["muted"], font=FONT_SUB).pack(anchor="w")
ramo_name_entry = tk.Entry(
    ramos_body, bg=THEME["field"], fg=THEME["text"], insertbackground=THEME["text"],
    relief="flat", highlightthickness=1, highlightbackground=THEME["border"], highlightcolor=THEME["accent"],
    font=("Segoe UI", 12),
)
ramo_name_entry.pack(fill="x", pady=(6, 10))

row_btns = tk.Frame(ramos_body, bg=THEME["card"])
row_btns.pack(fill="x")

tk.Button(row_btns, text="Agregar", command=add_ramo_ui, bg=THEME["btn"], fg=THEME["text"],
          relief="flat", padx=10, pady=8, font=("Segoe UI", 9, "bold")).pack(side="left")
tk.Button(row_btns, text="Renombrar", command=rename_ramo_ui, bg=THEME["btn"], fg=THEME["text"],
          relief="flat", padx=10, pady=8, font=("Segoe UI", 9, "bold")).pack(side="left", padx=8)
tk.Button(row_btns, text="Eliminar", command=delete_ramo_ui, bg=THEME["btn"], fg=THEME["text"],
          relief="flat", padx=10, pady=8, font=("Segoe UI", 9, "bold")).pack(side="left")

# Status bottom-left
status_label = tk.Label(panel, text="", bg=THEME["panel"], fg=THEME["muted"], font=FONT_BODY, wraplength=430, justify="left")
status_label.grid(row=4, column=0, sticky="ew", padx=(0, 16), pady=(10, 0))

# =========================
# UI — RIGHT (Historial)
# =========================
card_hist, hist_body = make_card(panel, "Historial (ramo activo)")
card_hist.grid(row=0, column=1, rowspan=5, sticky="nsew")

hist_body.grid_rowconfigure(1, weight=1)
hist_body.grid_columnconfigure(0, weight=1)

tk.Label(hist_body, text="Evaluaciones", bg=THEME["card"], fg=THEME["muted"], font=FONT_SUB)\
  .grid(row=0, column=0, sticky="w", pady=(0, 8))

list_frame = tk.Frame(hist_body, bg=THEME["card"])
list_frame.grid(row=1, column=0, sticky="nsew")
list_frame.grid_rowconfigure(0, weight=1)
list_frame.grid_columnconfigure(0, weight=1)

scroll = tk.Scrollbar(list_frame)
scroll.grid(row=0, column=1, sticky="ns")

listbox = tk.Listbox(
    list_frame, bg=THEME["field"], fg=THEME["text"],
    selectbackground=THEME["accent"], selectforeground="white",
    relief="flat", highlightthickness=1, highlightbackground=THEME["border"],
    font=("Segoe UI", 11), activestyle="none", yscrollcommand=scroll.set
)
listbox.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
scroll.config(command=listbox.yview)

tk.Label(hist_body, text="Nebu | N-Notas ©", bg=THEME["card"], fg=THEME["muted"], font=FONT_SUB)\
  .grid(row=2, column=0, sticky="w", pady=(10, 0))

# =========================
# Boot
# =========================
refresh_all()
refresh_nivel_ui()
nota_entry.focus_set()
set_status("Listo. Todo se calcula automáticamente.", THEME["muted"])
app.mainloop()