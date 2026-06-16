import unittest

from app.webhook_server import WebhookServer


class WebhookTests(unittest.TestCase):
    def test_webhook_creates_payload_with_default_state(self) -> None:
        captured = []
        server = WebhookServer(captured.append)
        client = server.app.test_client()

        response = client.post(
            "/webhook/card",
            json={
                "titulo": "Responder correo urgente",
                "descripcion": "Cliente solicita respuesta",
                "prioridad": "Alta",
            },
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(captured), 1)
        self.assertEqual(captured[0]["estado"], "No iniciado")


if __name__ == "__main__":
    unittest.main()
