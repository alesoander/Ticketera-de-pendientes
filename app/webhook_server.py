from __future__ import annotations

import threading
from typing import Callable

from flask import Flask, jsonify, request
from werkzeug.serving import make_server

from app.constants import ESTADOS, PRIORIDADES


class WebhookServer:
    """Servidor HTTP local para crear cards desde n8n."""

    def __init__(self, on_card_received: Callable[[dict], None], host: str = "127.0.0.1", port: int = 5000) -> None:
        self.host = host
        self.port = port
        self._on_card_received = on_card_received
        self._thread: threading.Thread | None = None
        self._server = None

        self.app = Flask(__name__)
        self._configure_routes()

    def _configure_routes(self) -> None:
        @self.app.post("/webhook/card")
        def receive_card():
            data = request.get_json(silent=True)
            if not isinstance(data, dict):
                return jsonify({"error": "JSON inválido."}), 400

            titulo = str(data.get("titulo", "")).strip()
            descripcion = str(data.get("descripcion", "")).strip()
            prioridad = str(data.get("prioridad", "")).strip()
            estado = str(data.get("estado", "No iniciado")).strip() or "No iniciado"

            if not titulo:
                return jsonify({"error": "El campo 'titulo' es obligatorio."}), 400
            if prioridad not in set(PRIORIDADES):
                return jsonify({"error": "Prioridad inválida. Use Alta, Media o Baja."}), 400
            if estado not in set(ESTADOS):
                return jsonify({"error": "Estado inválido. Use No iniciado, Pendiente o Terminado."}), 400

            payload = {
                "titulo": titulo,
                "descripcion": descripcion,
                "prioridad": prioridad,
                "estado": estado,
                "fecha_creacion": data.get("fecha_creacion"),
            }
            self._on_card_received(payload)
            return jsonify({"message": "Card creada correctamente."}), 201

        @self.app.get("/health")
        def health_check():
            return jsonify({"status": "ok"}), 200

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return

        self._server = make_server(self.host, self.port, self.app)
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        if self._server:
            self._server.shutdown()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)
