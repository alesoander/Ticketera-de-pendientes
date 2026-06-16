import tempfile
import unittest
from pathlib import Path

from app.database import CardDatabase


class CardDatabaseTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "cards.db"
        self.db = CardDatabase(self.db_path)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_create_card_defaults_and_active_filter(self) -> None:
        card_id = self.db.create_card("Tarea 1", "Descripción", "Alta")
        card = self.db.get_card(card_id)

        self.assertEqual(card["estado"], "No iniciado")
        self.assertIsNotNone(card["fecha_creacion"])
        self.assertIsNone(card["fecha_termino"])

        active_cards = self.db.list_active_cards()
        self.assertEqual(len(active_cards), 1)

    def test_move_to_history_and_delete(self) -> None:
        card_id = self.db.create_card("Tarea 2", "Descripción", "Media", "Pendiente")
        self.db.update_card(card_id, "Tarea 2", "Descripción", "Media", "Terminado")

        self.assertEqual(len(self.db.list_active_cards()), 0)
        historical = self.db.list_historical_cards()
        self.assertEqual(len(historical), 1)
        self.assertIsNotNone(historical[0]["fecha_termino"])

        self.db.delete_card(card_id)
        self.assertEqual(len(self.db.list_historical_cards()), 0)


if __name__ == "__main__":
    unittest.main()
