from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

PRIORIDADES = {"Alta", "Media", "Baja"}
ESTADOS = {"No iniciado", "Pendiente", "Terminado"}


class CardDatabase:
    """Persistencia local de cards usando SQLite."""

    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._create_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _create_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS cards (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    titulo TEXT NOT NULL,
                    descripcion TEXT NOT NULL,
                    prioridad TEXT NOT NULL CHECK (prioridad IN ('Alta', 'Media', 'Baja')),
                    estado TEXT NOT NULL CHECK (estado IN ('No iniciado', 'Pendiente', 'Terminado')),
                    fecha_creacion TEXT NOT NULL,
                    fecha_termino TEXT
                )
                """
            )

    @staticmethod
    def _now() -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def _validate_prioridad(prioridad: str) -> None:
        if prioridad not in PRIORIDADES:
            raise ValueError("Prioridad inválida. Use Alta, Media o Baja.")

    @staticmethod
    def _validate_estado(estado: str) -> None:
        if estado not in ESTADOS:
            raise ValueError("Estado inválido. Use No iniciado, Pendiente o Terminado.")

    def create_card(
        self,
        titulo: str,
        descripcion: str,
        prioridad: str,
        estado: str = "No iniciado",
        fecha_creacion: str | None = None,
    ) -> int:
        if not titulo.strip():
            raise ValueError("El título es obligatorio.")
        self._validate_prioridad(prioridad)
        self._validate_estado(estado)

        fecha_creacion_final = fecha_creacion or self._now()
        fecha_termino = self._now() if estado == "Terminado" else None

        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO cards (titulo, descripcion, prioridad, estado, fecha_creacion, fecha_termino)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    titulo.strip(),
                    descripcion.strip(),
                    prioridad,
                    estado,
                    fecha_creacion_final,
                    fecha_termino,
                ),
            )
            return int(cursor.lastrowid)

    def update_card(self, card_id: int, titulo: str, descripcion: str, prioridad: str, estado: str) -> None:
        if not titulo.strip():
            raise ValueError("El título es obligatorio.")
        self._validate_prioridad(prioridad)
        self._validate_estado(estado)

        card = self.get_card(card_id)
        fecha_termino = card["fecha_termino"]
        if estado == "Terminado" and not fecha_termino:
            fecha_termino = self._now()
        elif estado != "Terminado":
            fecha_termino = None

        with self._connect() as conn:
            conn.execute(
                """
                UPDATE cards
                SET titulo = ?, descripcion = ?, prioridad = ?, estado = ?, fecha_termino = ?
                WHERE id = ?
                """,
                (titulo.strip(), descripcion.strip(), prioridad, estado, fecha_termino, card_id),
            )

    def delete_card(self, card_id: int) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM cards WHERE id = ?", (card_id,))

    def get_card(self, card_id: int) -> dict[str, Any]:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM cards WHERE id = ?", (card_id,)).fetchone()
        if row is None:
            raise ValueError("Card no encontrada.")
        return dict(row)

    def list_active_cards(self, prioridad: str = "Todas", estado: str = "Todos") -> list[dict[str, Any]]:
        conditions = ["estado IN ('No iniciado', 'Pendiente')"]
        params: list[Any] = []

        if prioridad != "Todas":
            self._validate_prioridad(prioridad)
            conditions.append("prioridad = ?")
            params.append(prioridad)

        if estado != "Todos":
            if estado not in {"No iniciado", "Pendiente"}:
                raise ValueError("Filtro de estado inválido.")
            conditions.append("estado = ?")
            params.append(estado)

        where_clause = " AND ".join(conditions)
        query = f"""
            SELECT * FROM cards
            WHERE {where_clause}
            ORDER BY
                CASE prioridad WHEN 'Alta' THEN 1 WHEN 'Media' THEN 2 ELSE 3 END,
                fecha_creacion DESC
        """

        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [dict(row) for row in rows]

    def list_historical_cards(self) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM cards
                WHERE estado = 'Terminado'
                ORDER BY fecha_termino DESC, fecha_creacion DESC
                """
            ).fetchall()
        return [dict(row) for row in rows]
