from __future__ import annotations

import sys
from pathlib import Path


def _get_app_dir() -> Path:
    """Return the writable directory where app data (SQLite DB) should be stored.

    When running as a PyInstaller one-file bundle, ``sys.executable`` points to
    the ``.exe`` itself and ``sys._MEIPASS`` is a read-only temp extraction dir.
    We must therefore base the data path on the *executable's* parent directory,
    not on ``__file__``, so the SQLite database ends up next to the ``.exe`` in a
    location the user can write to and back up.
    """
    if getattr(sys, "frozen", False):
        # Packaged with PyInstaller: use the directory that contains the .exe
        return Path(sys.executable).parent
    # Running from source
    return Path(__file__).resolve().parent


def main() -> None:
    from app.database import CardDatabase
    from app.gui import TaskBoardApp

    app_dir = _get_app_dir()
    db_path = app_dir / "data" / "cards.db"

    db = CardDatabase(db_path)
    app = TaskBoardApp(db)
    app.mainloop()


if __name__ == "__main__":
    main()
