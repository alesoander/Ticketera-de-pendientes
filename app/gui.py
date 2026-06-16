from __future__ import annotations

import queue
import tkinter as tk
from tkinter import messagebox, ttk

from app.constants import ESTADOS, ESTADOS_ACTIVOS, PRIORIDADES
from app.database import CardDatabase
from app.webhook_server import WebhookServer

PRIORIDAD_COLORES = {
    "Alta": "#d9534f",
    "Media": "#f0ad4e",
    "Baja": "#5cb85c",
}


class CardForm(tk.Toplevel):
    def __init__(self, parent: "TaskBoardApp", db: CardDatabase, card_id: int | None = None) -> None:
        super().__init__(parent)
        self.parent = parent
        self.db = db
        self.card_id = card_id
        self.title("Editar card" if card_id else "Nueva card")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self._build_ui()
        if card_id:
            self._load_card(card_id)

    def _build_ui(self) -> None:
        container = ttk.Frame(self, padding=12)
        container.grid(row=0, column=0, sticky="nsew")

        ttk.Label(container, text="Título").grid(row=0, column=0, sticky="w")
        self.title_var = tk.StringVar()
        ttk.Entry(container, textvariable=self.title_var, width=45).grid(row=1, column=0, sticky="ew", pady=(0, 8))

        ttk.Label(container, text="Descripción").grid(row=2, column=0, sticky="w")
        self.description_text = tk.Text(container, width=45, height=6)
        self.description_text.grid(row=3, column=0, sticky="ew", pady=(0, 8))

        row = ttk.Frame(container)
        row.grid(row=4, column=0, sticky="ew", pady=(0, 8))
        row.columnconfigure(0, weight=1)
        row.columnconfigure(1, weight=1)

        ttk.Label(row, text="Prioridad").grid(row=0, column=0, sticky="w")
        ttk.Label(row, text="Estado").grid(row=0, column=1, sticky="w")

        self.priority_var = tk.StringVar(value="Media")
        self.state_var = tk.StringVar(value="No iniciado")

        ttk.Combobox(row, textvariable=self.priority_var, values=list(PRIORIDADES), state="readonly").grid(
            row=1, column=0, sticky="ew", padx=(0, 8)
        )
        ttk.Combobox(
            row,
            textvariable=self.state_var,
            values=list(ESTADOS),
            state="readonly",
        ).grid(row=1, column=1, sticky="ew")

        button_row = ttk.Frame(container)
        button_row.grid(row=5, column=0, sticky="e")
        ttk.Button(button_row, text="Guardar", command=self._save).grid(row=0, column=0, padx=(0, 6))
        ttk.Button(button_row, text="Cancelar", command=self.destroy).grid(row=0, column=1)

    def _load_card(self, card_id: int) -> None:
        card = self.db.get_card(card_id)
        self.title_var.set(card["titulo"])
        self.description_text.insert("1.0", card["descripcion"])
        self.priority_var.set(card["prioridad"])
        self.state_var.set(card["estado"])

    def _save(self) -> None:
        titulo = self.title_var.get().strip()
        descripcion = self.description_text.get("1.0", "end").strip()
        prioridad = self.priority_var.get()
        estado = self.state_var.get()

        try:
            if self.card_id:
                self.db.update_card(self.card_id, titulo, descripcion, prioridad, estado)
            else:
                self.db.create_card(titulo, descripcion, prioridad, estado)
        except ValueError as exc:
            messagebox.showerror("Error", str(exc), parent=self)
            return

        self.parent.refresh_tables()
        self.destroy()


class TaskBoardApp(tk.Tk):
    def __init__(self, db: CardDatabase, webhook_host: str = "127.0.0.1", webhook_port: int = 5000) -> None:
        super().__init__()
        self.db = db
        self.title("Ticketera de Pendientes")
        self.geometry("1000x620")

        self.webhook_queue: queue.Queue[dict] = queue.Queue()
        self.webhook_server = WebhookServer(self.webhook_queue.put, host=webhook_host, port=webhook_port)

        self._build_ui()
        self.refresh_tables()

        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.webhook_server.start()
        self.after(500, self._process_webhook_queue)

    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        notebook = ttk.Notebook(self)
        notebook.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)

        self.active_frame = ttk.Frame(notebook)
        self.history_frame = ttk.Frame(notebook)
        notebook.add(self.active_frame, text="Cards activas")
        notebook.add(self.history_frame, text="Histórico")

        self._build_active_tab()
        self._build_history_tab()

        self.status_var = tk.StringVar(value="Webhook activo en http://127.0.0.1:5000/webhook/card")
        ttk.Label(self, textvariable=self.status_var, relief="sunken", anchor="w", padding=6).grid(
            row=1, column=0, sticky="ew"
        )

    def _build_active_tab(self) -> None:
        self.active_frame.columnconfigure(0, weight=1)
        self.active_frame.rowconfigure(1, weight=1)

        top = ttk.Frame(self.active_frame)
        top.grid(row=0, column=0, sticky="ew", pady=(0, 8))

        ttk.Label(top, text="Prioridad:").grid(row=0, column=0, padx=(0, 4))
        self.priority_filter = tk.StringVar(value="Todas")
        ttk.Combobox(top, textvariable=self.priority_filter, values=["Todas", *PRIORIDADES], width=12, state="readonly").grid(
            row=0, column=1, padx=(0, 8)
        )

        ttk.Label(top, text="Estado:").grid(row=0, column=2, padx=(0, 4))
        self.state_filter = tk.StringVar(value="Todos")
        ttk.Combobox(
            top,
            textvariable=self.state_filter,
            values=["Todos", *ESTADOS_ACTIVOS],
            width=14,
            state="readonly",
        ).grid(row=0, column=3, padx=(0, 12))

        ttk.Button(top, text="Aplicar filtros", command=self.refresh_active).grid(row=0, column=4, padx=2)
        ttk.Button(top, text="Nueva card", command=self.create_card).grid(row=0, column=5, padx=2)
        ttk.Button(top, text="Editar", command=self.edit_selected_active).grid(row=0, column=6, padx=2)
        ttk.Button(top, text="Cambiar estado", command=self.change_state_selected).grid(row=0, column=7, padx=2)
        ttk.Button(top, text="Eliminar", command=self.delete_selected_active).grid(row=0, column=8, padx=2)

        columns = ("id", "titulo", "descripcion", "prioridad", "estado", "fecha_creacion")
        self.active_tree = ttk.Treeview(self.active_frame, columns=columns, show="headings", height=18)
        for col in columns:
            self.active_tree.heading(col, text=col.replace("_", " ").title())
        self.active_tree.column("id", width=50, anchor="center")
        self.active_tree.column("titulo", width=240)
        self.active_tree.column("descripcion", width=320)
        self.active_tree.column("prioridad", width=100, anchor="center")
        self.active_tree.column("estado", width=120, anchor="center")
        self.active_tree.column("fecha_creacion", width=140, anchor="center")
        self.active_tree.grid(row=1, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(self.active_frame, orient="vertical", command=self.active_tree.yview)
        self.active_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=1, column=1, sticky="ns")

        for prioridad, color in PRIORIDAD_COLORES.items():
            self.active_tree.tag_configure(prioridad, foreground=color)

    def _build_history_tab(self) -> None:
        self.history_frame.columnconfigure(0, weight=1)
        self.history_frame.rowconfigure(1, weight=1)

        top = ttk.Frame(self.history_frame)
        top.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        ttk.Button(top, text="Refrescar", command=self.refresh_history).grid(row=0, column=0, padx=(0, 8))
        ttk.Button(top, text="Eliminar", command=self.delete_selected_history).grid(row=0, column=1)

        columns = ("id", "titulo", "descripcion", "prioridad", "fecha_creacion", "fecha_termino")
        self.history_tree = ttk.Treeview(self.history_frame, columns=columns, show="headings", height=18)
        for col in columns:
            self.history_tree.heading(col, text=col.replace("_", " ").title())
        self.history_tree.column("id", width=50, anchor="center")
        self.history_tree.column("titulo", width=240)
        self.history_tree.column("descripcion", width=320)
        self.history_tree.column("prioridad", width=100, anchor="center")
        self.history_tree.column("fecha_creacion", width=140, anchor="center")
        self.history_tree.column("fecha_termino", width=140, anchor="center")
        self.history_tree.grid(row=1, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(self.history_frame, orient="vertical", command=self.history_tree.yview)
        self.history_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=1, column=1, sticky="ns")

        for prioridad, color in PRIORIDAD_COLORES.items():
            self.history_tree.tag_configure(prioridad, foreground=color)

    def _process_webhook_queue(self) -> None:
        updated = False
        while not self.webhook_queue.empty():
            payload = self.webhook_queue.get()
            try:
                self.db.create_card(
                    payload["titulo"],
                    payload.get("descripcion", ""),
                    payload["prioridad"],
                    payload.get("estado", "No iniciado"),
                    payload.get("fecha_creacion"),
                )
                updated = True
            except ValueError as exc:
                self.status_var.set(f"Error al crear card de webhook: {exc}")

        if updated:
            self.refresh_tables()
            self.status_var.set("Se creó una card desde webhook.")

        self.after(500, self._process_webhook_queue)

    def refresh_tables(self) -> None:
        self.refresh_active()
        self.refresh_history()

    def refresh_active(self) -> None:
        for row in self.active_tree.get_children():
            self.active_tree.delete(row)

        cards = self.db.list_active_cards(self.priority_filter.get(), self.state_filter.get())
        for card in cards:
            self.active_tree.insert(
                "",
                "end",
                values=(
                    card["id"],
                    card["titulo"],
                    card["descripcion"],
                    card["prioridad"],
                    card["estado"],
                    card["fecha_creacion"],
                ),
                tags=(card["prioridad"],),
            )

    def refresh_history(self) -> None:
        for row in self.history_tree.get_children():
            self.history_tree.delete(row)

        cards = self.db.list_historical_cards()
        for card in cards:
            self.history_tree.insert(
                "",
                "end",
                values=(
                    card["id"],
                    card["titulo"],
                    card["descripcion"],
                    card["prioridad"],
                    card["fecha_creacion"],
                    card["fecha_termino"] or "",
                ),
                tags=(card["prioridad"],),
            )

    def create_card(self) -> None:
        CardForm(self, self.db)

    def _selected_id(self, tree: ttk.Treeview) -> int | None:
        item = tree.selection()
        if not item:
            return None
        return int(tree.item(item[0], "values")[0])

    def edit_selected_active(self) -> None:
        card_id = self._selected_id(self.active_tree)
        if card_id is None:
            messagebox.showwarning("Atención", "Seleccione una card activa para editar.")
            return
        CardForm(self, self.db, card_id)

    def change_state_selected(self) -> None:
        card_id = self._selected_id(self.active_tree)
        if card_id is None:
            messagebox.showwarning("Atención", "Seleccione una card para cambiar su estado.")
            return

        card = self.db.get_card(card_id)
        options = list(ESTADOS)
        next_state = options[(options.index(card["estado"]) + 1) % len(options)]
        self.db.update_card(card_id, card["titulo"], card["descripcion"], card["prioridad"], next_state)
        self.refresh_tables()

    def _delete_card(self, card_id: int) -> None:
        confirm = messagebox.askyesno(
            "Confirmar eliminación",
            "Esta acción eliminará la card permanentemente del almacenamiento local. ¿Continuar?",
        )
        if not confirm:
            return
        self.db.delete_card(card_id)
        self.refresh_tables()

    def delete_selected_active(self) -> None:
        card_id = self._selected_id(self.active_tree)
        if card_id is None:
            messagebox.showwarning("Atención", "Seleccione una card activa para eliminar.")
            return
        self._delete_card(card_id)

    def delete_selected_history(self) -> None:
        card_id = self._selected_id(self.history_tree)
        if card_id is None:
            messagebox.showwarning("Atención", "Seleccione una card del histórico para eliminar.")
            return
        self._delete_card(card_id)

    def on_close(self) -> None:
        self.webhook_server.stop()
        self.destroy()
