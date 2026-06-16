from __future__ import annotations

from pathlib import Path

from app.database import CardDatabase
from app.gui import TaskBoardApp


def main() -> None:
    project_root = Path(__file__).resolve().parent
    db_path = project_root / "data" / "cards.db"

    db = CardDatabase(db_path)
    app = TaskBoardApp(db)
    app.mainloop()


if __name__ == "__main__":
    main()
