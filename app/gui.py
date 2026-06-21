from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from app.constants import ESTADOS, ESTADOS_ACTIVOS, PRIORIDADES
from app.database import CardDatabase

# ─── Color palette (inspired by ui-test-copy / shadcn zinc theme) ─────────────
BG = "#f4f4f5"          # zinc-50 background
WHITE = "#ffffff"
BORDER = "#e4e4e7"      # zinc-200 border
TEXT_MAIN = "#18181b"   # zinc-900 primary text
TEXT_SUB = "#71717a"    # zinc-500 secondary text

PRIORITY_BORDER: dict[str, str] = {
    "Alta": "#ef4444",
    "Media": "#f97316",
    "Baja": "#3b82f6",
}
PRIORITY_BADGE_BG: dict[str, str] = {
    "Alta": "#fee2e2",
    "Media": "#ffedd5",
    "Baja": "#dbeafe",
}
PRIORITY_BADGE_FG: dict[str, str] = {
    "Alta": "#b91c1c",
    "Media": "#c2410c",
    "Baja": "#1d4ed8",
}
STATUS_BADGE_BG: dict[str, str] = {
    "No iniciado": "#f4f4f5",
    "Pendiente": "#fef9c3",
    "Terminado": "#dcfce7",
}
STATUS_BADGE_FG: dict[str, str] = {
    "No iniciado": "#3f3f46",
    "Pendiente": "#a16207",
    "Terminado": "#15803d",
}

FONT_TITLE = ("Segoe UI", 16, "bold")
FONT_SECTION = ("Segoe UI", 14, "bold")
FONT_SUBTITLE = ("Segoe UI", 10)
FONT_CARD_TITLE = ("Segoe UI", 10, "bold")
FONT_CARD_DESC = ("Segoe UI", 9)
FONT_BADGE = ("Segoe UI", 8, "bold")
FONT_LABEL = ("Segoe UI", 10)
FONT_BTN = ("Segoe UI", 10)

# ─── Layout constants ─────────────────────────────────────────────────────────
WINDOW_WIDTH = 1100
WINDOW_HEIGHT = 680
WINDOW_MIN_WIDTH = 820
WINDOW_MIN_HEIGHT = 500
CARD_TITLE_WRAP = 360    # px – wraplength for card titles
CARD_DESC_WRAP = 370     # px – wraplength for card descriptions
CARD_DESC_MAX_LEN = 100  # chars – truncate description beyond this length


class _ScrollableFrame(tk.Frame):
    """A vertically scrollable container. Access child widgets via ``.inner``."""

    def __init__(self, parent: tk.Widget, **kwargs: object) -> None:
        bg: str = str(kwargs.pop("bg", BG))
        super().__init__(parent, bg=bg, **kwargs)  # type: ignore[arg-type]

        self._canvas = tk.Canvas(self, bg=bg, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        self._canvas.pack(side="left", fill="both", expand=True)

        self.inner = tk.Frame(self._canvas, bg=bg)
        self._win_id = self._canvas.create_window((0, 0), window=self.inner, anchor="nw")

        self.inner.bind("<Configure>", self._on_inner_configure)
        self._canvas.bind("<Configure>", self._on_canvas_configure)
        self._canvas.bind("<Enter>", lambda _e: self._canvas.bind_all("<MouseWheel>", self._on_mousewheel))
        self._canvas.bind("<Leave>", lambda _e: self._canvas.unbind_all("<MouseWheel>"))

    def _on_inner_configure(self, _event: tk.Event) -> None:  # type: ignore[type-arg]
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))

    def _on_canvas_configure(self, event: tk.Event) -> None:  # type: ignore[type-arg]
        self._canvas.itemconfig(self._win_id, width=event.width)

    def _on_mousewheel(self, event: tk.Event) -> None:  # type: ignore[type-arg]
        self._canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def scroll_to_top(self) -> None:
        self._canvas.yview_moveto(0)


class CardForm(tk.Toplevel):
    """Modal dialog for creating or editing a task card."""

    def __init__(
        self,
        parent: "TaskBoardApp",
        db: CardDatabase,
        card_id: int | None = None,
    ) -> None:
        super().__init__(parent)
        self.parent = parent
        self.db = db
        self.card_id = card_id
        self.configure(bg=WHITE)
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        self._build_ui()
        if card_id:
            self._load_card(card_id)
        self._center_on_parent()

    def _center_on_parent(self) -> None:
        self.update_idletasks()
        pw = self.parent.winfo_x() + self.parent.winfo_width() // 2
        ph = self.parent.winfo_y() + self.parent.winfo_height() // 2
        w, h = self.winfo_width(), self.winfo_height()
        self.geometry(f"+{pw - w // 2}+{ph - h // 2}")

    def _build_ui(self) -> None:
        dialog_title = "Editar tarea" if self.card_id else "Nueva tarea"
        self.wm_title(dialog_title)

        # Header
        tk.Label(
            self, text=dialog_title,
            bg=WHITE, fg=TEXT_MAIN, font=FONT_SECTION, anchor="w",
        ).pack(fill="x", padx=24, pady=(20, 16))
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x")

        # Form body
        body = tk.Frame(self, bg=WHITE)
        body.pack(fill="both", expand=True, padx=24, pady=16)

        tk.Label(body, text="Título *", bg=WHITE, fg=TEXT_MAIN, font=FONT_LABEL, anchor="w").pack(fill="x", pady=(0, 4))
        self.title_var = tk.StringVar()
        tk.Entry(
            body, textvariable=self.title_var,
            bg=WHITE, fg=TEXT_MAIN, insertbackground=TEXT_MAIN,
            font=FONT_LABEL, relief="solid", bd=1, width=52,
        ).pack(fill="x", pady=(0, 12))

        tk.Label(body, text="Descripción", bg=WHITE, fg=TEXT_MAIN, font=FONT_LABEL, anchor="w").pack(fill="x", pady=(0, 4))
        self.description_text = tk.Text(
            body,
            bg=WHITE, fg=TEXT_MAIN, insertbackground=TEXT_MAIN,
            font=FONT_LABEL, relief="solid", bd=1,
            width=52, height=5, wrap="word",
        )
        self.description_text.pack(fill="x", pady=(0, 12))

        # Priority + State side by side
        row = tk.Frame(body, bg=WHITE)
        row.pack(fill="x", pady=(0, 16))
        row.columnconfigure(0, weight=1)
        row.columnconfigure(1, weight=1)

        pri = tk.Frame(row, bg=WHITE)
        pri.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        tk.Label(pri, text="Prioridad", bg=WHITE, fg=TEXT_MAIN, font=FONT_LABEL, anchor="w").pack(fill="x", pady=(0, 4))
        self.priority_var = tk.StringVar(value="Media")
        ttk.Combobox(pri, textvariable=self.priority_var, values=list(PRIORIDADES), state="readonly").pack(fill="x")

        sta = tk.Frame(row, bg=WHITE)
        sta.grid(row=0, column=1, sticky="ew")
        tk.Label(sta, text="Estado", bg=WHITE, fg=TEXT_MAIN, font=FONT_LABEL, anchor="w").pack(fill="x", pady=(0, 4))
        self.state_var = tk.StringVar(value="No iniciado")
        ttk.Combobox(sta, textvariable=self.state_var, values=list(ESTADOS), state="readonly").pack(fill="x")

        # Footer with action buttons
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x")
        footer = tk.Frame(self, bg=WHITE)
        footer.pack(fill="x", padx=24, pady=14)

        tk.Button(
            footer, text="Guardar",
            bg=TEXT_MAIN, fg=WHITE, activebackground="#3f3f46", activeforeground=WHITE,
            font=FONT_BTN, relief="flat", padx=16, pady=6, cursor="hand2",
            command=self._save,
        ).pack(side="right", padx=(8, 0))

        tk.Button(
            footer, text="Cancelar",
            bg=BG, fg=TEXT_MAIN, activebackground=BORDER, activeforeground=TEXT_MAIN,
            font=FONT_BTN, relief="flat", padx=16, pady=6, cursor="hand2",
            command=self.destroy,
        ).pack(side="right")

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
        self.parent.refresh_all()
        self.destroy()


class TaskBoardApp(tk.Tk):
    """Main application window with a card-based UI."""

    def __init__(self, db: CardDatabase) -> None:
        super().__init__()
        self.db = db
        self.title("Gestor de Tareas")
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.configure(bg=BG)
        self.minsize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)

        self._priority_filter = tk.StringVar(value="Todas")
        self._state_filter = tk.StringVar(value="Todos")
        self._hist_priority_filter = tk.StringVar(value="Todas")

        self._build_ui()
        self.refresh_all()

    # ── Layout builders ──────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)
        self._build_header()
        self._build_content()

    def _build_header(self) -> None:
        header = tk.Frame(self, bg=WHITE, height=58)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_propagate(False)
        header.columnconfigure(1, weight=1)

        # Bottom border line
        tk.Frame(header, bg=BORDER, height=1).place(relx=0, rely=1.0, anchor="sw", relwidth=1.0)

        tk.Label(
            header, text="Gestor de Tareas",
            bg=WHITE, fg=TEXT_MAIN, font=FONT_TITLE,
        ).grid(row=0, column=0, padx=24, pady=10, sticky="w")

        nav = tk.Frame(header, bg=WHITE)
        nav.grid(row=0, column=1, sticky="e", padx=24)

        self._btn_nav_active = tk.Button(
            nav, text="Activas",
            bg=TEXT_MAIN, fg=WHITE, activebackground="#3f3f46", activeforeground=WHITE,
            font=FONT_BTN, relief="flat", padx=16, pady=6, cursor="hand2",
            command=self._show_active,
        )
        self._btn_nav_active.pack(side="left", padx=(0, 4))

        self._btn_nav_history = tk.Button(
            nav, text="Histórico",
            bg=BG, fg=TEXT_SUB, activebackground=BORDER, activeforeground=TEXT_MAIN,
            font=FONT_BTN, relief="flat", padx=16, pady=6, cursor="hand2",
            command=self._show_history,
        )
        self._btn_nav_history.pack(side="left")

    def _build_content(self) -> None:
        content = tk.Frame(self, bg=BG)
        content.grid(row=1, column=0, sticky="nsew")
        content.columnconfigure(0, weight=1)
        content.rowconfigure(0, weight=1)

        self._view_active = tk.Frame(content, bg=BG)
        self._view_active.grid(row=0, column=0, sticky="nsew")
        self._build_active_view(self._view_active)

        self._view_history = tk.Frame(content, bg=BG)
        self._view_history.grid(row=0, column=0, sticky="nsew")
        self._build_history_view(self._view_history)

        self._view_active.tkraise()

    def _build_active_view(self, parent: tk.Frame) -> None:
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(2, weight=1)

        # Title row
        title_row = tk.Frame(parent, bg=BG)
        title_row.grid(row=0, column=0, sticky="ew", padx=24, pady=(20, 0))
        title_row.columnconfigure(0, weight=1)

        left = tk.Frame(title_row, bg=BG)
        left.grid(row=0, column=0, sticky="w")
        tk.Label(left, text="Tareas Activas", bg=BG, fg=TEXT_MAIN, font=FONT_SECTION).pack(anchor="w")
        self._active_count_lbl = tk.Label(left, text="", bg=BG, fg=TEXT_SUB, font=FONT_SUBTITLE)
        self._active_count_lbl.pack(anchor="w")

        tk.Button(
            title_row, text="+ Nueva tarea",
            bg=TEXT_MAIN, fg=WHITE, activebackground="#3f3f46", activeforeground=WHITE,
            font=FONT_BTN, relief="flat", padx=16, pady=8, cursor="hand2",
            command=self.create_card,
        ).grid(row=0, column=1, sticky="e")

        # Filter bar
        fbar = tk.Frame(parent, bg=WHITE, highlightthickness=1, highlightbackground=BORDER)
        fbar.grid(row=1, column=0, sticky="ew", padx=24, pady=12)

        tk.Label(fbar, text="Filtrar:", bg=WHITE, fg=TEXT_SUB, font=FONT_LABEL).pack(side="left", padx=(14, 10), pady=10)
        tk.Label(fbar, text="Prioridad", bg=WHITE, fg=TEXT_MAIN, font=FONT_LABEL).pack(side="left", pady=10)
        ttk.Combobox(
            fbar, textvariable=self._priority_filter,
            values=["Todas", *PRIORIDADES], state="readonly", width=12,
        ).pack(side="left", padx=(4, 14), pady=10)

        tk.Label(fbar, text="Estado", bg=WHITE, fg=TEXT_MAIN, font=FONT_LABEL).pack(side="left", pady=10)
        ttk.Combobox(
            fbar, textvariable=self._state_filter,
            values=["Todos", *ESTADOS_ACTIVOS], state="readonly", width=14,
        ).pack(side="left", padx=(4, 14), pady=10)

        tk.Button(
            fbar, text="Aplicar",
            bg=BG, fg=TEXT_MAIN, activebackground=BORDER, activeforeground=TEXT_MAIN,
            font=FONT_BTN, relief="flat", padx=10, pady=4, cursor="hand2",
            command=self.refresh_active,
        ).pack(side="left", pady=10)

        # Scrollable card grid
        self._active_cards = _ScrollableFrame(parent, bg=BG)
        self._active_cards.grid(row=2, column=0, sticky="nsew", padx=24, pady=(0, 16))
        self._active_cards.inner.columnconfigure(0, weight=1)
        self._active_cards.inner.columnconfigure(1, weight=1)

    def _build_history_view(self, parent: tk.Frame) -> None:
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(2, weight=1)

        # Title row
        title_row = tk.Frame(parent, bg=BG)
        title_row.grid(row=0, column=0, sticky="ew", padx=24, pady=(20, 0))
        title_row.columnconfigure(0, weight=1)

        left = tk.Frame(title_row, bg=BG)
        left.grid(row=0, column=0, sticky="w")
        tk.Label(left, text="Histórico de Tareas", bg=BG, fg=TEXT_MAIN, font=FONT_SECTION).pack(anchor="w")
        self._history_count_lbl = tk.Label(left, text="", bg=BG, fg=TEXT_SUB, font=FONT_SUBTITLE)
        self._history_count_lbl.pack(anchor="w")

        # Filter bar
        fbar = tk.Frame(parent, bg=WHITE, highlightthickness=1, highlightbackground=BORDER)
        fbar.grid(row=1, column=0, sticky="ew", padx=24, pady=12)

        tk.Label(fbar, text="Filtrar:", bg=WHITE, fg=TEXT_SUB, font=FONT_LABEL).pack(side="left", padx=(14, 10), pady=10)
        tk.Label(fbar, text="Prioridad", bg=WHITE, fg=TEXT_MAIN, font=FONT_LABEL).pack(side="left", pady=10)
        ttk.Combobox(
            fbar, textvariable=self._hist_priority_filter,
            values=["Todas", *PRIORIDADES], state="readonly", width=12,
        ).pack(side="left", padx=(4, 14), pady=10)

        tk.Button(
            fbar, text="Aplicar",
            bg=BG, fg=TEXT_MAIN, activebackground=BORDER, activeforeground=TEXT_MAIN,
            font=FONT_BTN, relief="flat", padx=10, pady=4, cursor="hand2",
            command=self.refresh_history,
        ).pack(side="left", pady=10)

        # Scrollable card grid
        self._history_cards = _ScrollableFrame(parent, bg=BG)
        self._history_cards.grid(row=2, column=0, sticky="nsew", padx=24, pady=(0, 16))
        self._history_cards.inner.columnconfigure(0, weight=1)
        self._history_cards.inner.columnconfigure(1, weight=1)

    # ── Navigation ───────────────────────────────────────────────────────────

    def _show_active(self) -> None:
        self._view_active.tkraise()
        self._btn_nav_active.configure(bg=TEXT_MAIN, fg=WHITE)
        self._btn_nav_history.configure(bg=BG, fg=TEXT_SUB)

    def _show_history(self) -> None:
        self._view_history.tkraise()
        self._btn_nav_history.configure(bg=TEXT_MAIN, fg=WHITE)
        self._btn_nav_active.configure(bg=BG, fg=TEXT_SUB)

    # ── Card widget factory ───────────────────────────────────────────────────

    def _make_card(self, parent: tk.Widget, card: dict, *, is_history: bool = False) -> tk.Frame:
        """Build and return a styled card Frame for the given card data."""
        card_id: int = card["id"]
        prioridad: str = card["prioridad"]

        # Outer container: white background with thin zinc border
        container = tk.Frame(parent, bg=WHITE, highlightthickness=1, highlightbackground=BORDER)

        # Left priority color strip (4 px wide)
        tk.Frame(container, bg=PRIORITY_BORDER[prioridad], width=4).pack(side="left", fill="y")

        # Card body
        body = tk.Frame(container, bg=WHITE)
        body.pack(side="left", fill="both", expand=True, padx=12, pady=10)

        # ── Top row: title + actions menu ────────────────────────────────────
        top = tk.Frame(body, bg=WHITE)
        top.pack(fill="x")

        tk.Label(
            top, text=card["titulo"],
            bg=WHITE, fg=TEXT_MAIN, font=FONT_CARD_TITLE,
            anchor="w", justify="left", wraplength=CARD_TITLE_WRAP,
        ).pack(side="left", fill="x", expand=True)

        actions_btn = tk.Menubutton(
            top, text="⋮",
            bg=WHITE, fg=TEXT_SUB, activebackground=BG, activeforeground=TEXT_MAIN,
            font=("Segoe UI", 13), relief="flat", cursor="hand2", padx=4, pady=0,
        )
        actions_btn.pack(side="right", padx=(4, 0))

        actions_menu = tk.Menu(actions_btn, tearoff=0, font=FONT_LABEL)
        actions_menu.add_command(label="Editar", command=lambda c=card_id: self._edit_card(c))
        actions_menu.add_separator()
        actions_menu.add_command(
            label="Eliminar",
            foreground="#ef4444",
            command=lambda c=card_id: self._delete_card(c),
        )
        actions_btn.configure(menu=actions_menu)

        # ── Description (truncated to 100 chars) ─────────────────────────────
        desc = (card.get("descripcion") or "").strip()
        if desc:
            display = (desc[: CARD_DESC_MAX_LEN - 3] + "…") if len(desc) > CARD_DESC_MAX_LEN else desc
            tk.Label(
                body, text=display,
                bg=WHITE, fg=TEXT_SUB, font=FONT_CARD_DESC,
                anchor="w", justify="left", wraplength=CARD_DESC_WRAP,
            ).pack(fill="x", pady=(4, 6))
        else:
            tk.Frame(body, bg=WHITE, height=6).pack()

        # ── Badges row ───────────────────────────────────────────────────────
        badge_row = tk.Frame(body, bg=WHITE)
        badge_row.pack(fill="x")

        tk.Label(
            badge_row, text=prioridad,
            bg=PRIORITY_BADGE_BG[prioridad], fg=PRIORITY_BADGE_FG[prioridad],
            font=FONT_BADGE, padx=7, pady=2, relief="flat",
        ).pack(side="left")

        # Status badge as a Menubutton so users can change state directly
        estado: str = card["estado"]
        status_btn = tk.Menubutton(
            badge_row, text=estado,
            bg=STATUS_BADGE_BG.get(estado, BG), fg=STATUS_BADGE_FG.get(estado, TEXT_MAIN),
            activebackground=STATUS_BADGE_BG.get(estado, BG),
            activeforeground=STATUS_BADGE_FG.get(estado, TEXT_MAIN),
            font=FONT_BADGE, padx=7, pady=2, relief="flat", cursor="hand2",
        )
        status_btn.pack(side="left", padx=(6, 0))

        status_menu = tk.Menu(status_btn, tearoff=0, font=FONT_LABEL)
        for s in ESTADOS:
            status_menu.add_command(label=s, command=lambda c=card_id, sv=s: self._change_state(c, sv))
        status_btn.configure(menu=status_menu)

        # ── Dates (history cards only) ────────────────────────────────────────
        if is_history:
            parts: list[str] = []
            if card.get("fecha_creacion"):
                parts.append(f"Creado: {card['fecha_creacion'][:10]}")
            if card.get("fecha_termino"):
                parts.append(f"Completado: {card['fecha_termino'][:10]}")
            if parts:
                tk.Label(
                    body, text="  ·  ".join(parts),
                    bg=WHITE, fg=TEXT_SUB, font=FONT_CARD_DESC, anchor="w",
                ).pack(fill="x", pady=(6, 0))

        return container

    def _render_empty_state(self, inner: tk.Widget, total: int) -> None:
        """Render an empty-state placeholder inside *inner*."""
        if total == 0:
            msg = "No hay tareas aquí"
            sub = "Las tareas creadas aparecerán en esta sección"
        else:
            msg = "No hay tareas con estos filtros"
            sub = "Prueba con otros filtros o limpia la selección"

        frame = tk.Frame(inner, bg=BG)
        frame.grid(row=0, column=0, columnspan=2, pady=48, padx=20)
        tk.Label(frame, text="📋", bg=BG, fg=TEXT_SUB, font=("Segoe UI", 32)).pack()
        tk.Label(frame, text=msg, bg=BG, fg=TEXT_MAIN, font=FONT_SECTION).pack(pady=(12, 4))
        tk.Label(frame, text=sub, bg=BG, fg=TEXT_SUB, font=FONT_SUBTITLE).pack()

    # ── Data refresh ─────────────────────────────────────────────────────────

    def refresh_all(self) -> None:
        self.refresh_active()
        self.refresh_history()

    def refresh_active(self) -> None:
        for w in self._active_cards.inner.winfo_children():
            w.destroy()

        all_active = self.db.list_active_cards()
        filtered = self.db.list_active_cards(self._priority_filter.get(), self._state_filter.get())

        count = len(all_active)
        noun = "tarea pendiente" if count == 1 else "tareas pendientes"
        self._active_count_lbl.configure(text=f"{count} {noun}")

        if not filtered:
            self._render_empty_state(self._active_cards.inner, count)
        else:
            for i, card in enumerate(filtered):
                widget = self._make_card(self._active_cards.inner, card, is_history=False)
                widget.grid(row=i // 2, column=i % 2, sticky="nsew", padx=6, pady=6)

        self._active_cards.scroll_to_top()

    def refresh_history(self) -> None:
        for w in self._history_cards.inner.winfo_children():
            w.destroy()

        all_hist = self.db.list_historical_cards()
        hist_pri = self._hist_priority_filter.get()
        filtered = all_hist if hist_pri == "Todas" else [c for c in all_hist if c["prioridad"] == hist_pri]

        count = len(all_hist)
        noun = "tarea completada" if count == 1 else "tareas completadas"
        self._history_count_lbl.configure(text=f"{count} {noun}")

        if not filtered:
            self._render_empty_state(self._history_cards.inner, count)
        else:
            for i, card in enumerate(filtered):
                widget = self._make_card(self._history_cards.inner, card, is_history=True)
                widget.grid(row=i // 2, column=i % 2, sticky="nsew", padx=6, pady=6)

        self._history_cards.scroll_to_top()

    # ── Actions ──────────────────────────────────────────────────────────────

    def create_card(self) -> None:
        CardForm(self, self.db)

    def _edit_card(self, card_id: int) -> None:
        CardForm(self, self.db, card_id)

    def _delete_card(self, card_id: int) -> None:
        if messagebox.askyesno(
            "Confirmar eliminación",
            "Esta acción eliminará la tarea permanentemente. ¿Continuar?",
        ):
            self.db.delete_card(card_id)
            self.refresh_all()

    def _change_state(self, card_id: int, new_state: str) -> None:
        card = self.db.get_card(card_id)
        self.db.update_card(card_id, card["titulo"], card["descripcion"], card["prioridad"], new_state)
        self.refresh_all()
