# -*- mode: python ; coding: utf-8 -*-
#
# PyInstaller spec for Ticketera de Pendientes.
#
# Build with:
#   pyinstaller ticketera.spec
#
# The resulting one-file executable is written to:
#   dist/ticketera.exe

block_cipher = None

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        # Flask and its dependencies are not always auto-detected by PyInstaller
        "flask",
        "flask.json.provider",
        "flask.app",
        "jinja2",
        "jinja2.ext",
        "click",
        "werkzeug",
        "werkzeug.serving",
        "werkzeug.debug",
        "werkzeug.exceptions",
        "werkzeug.routing",
        "werkzeug.routing.rules",
        "werkzeug.routing.map",
        "werkzeug.wrappers",
        "werkzeug.wrappers.request",
        "werkzeug.wrappers.response",
        "werkzeug.middleware",
        "werkzeug.middleware.proxy_fix",
        "werkzeug.sansio",
        "werkzeug.sansio.utils",
        "itsdangerous",
        # tkinter is usually bundled on Windows; include explicitly to be safe
        "tkinter",
        "tkinter.ttk",
        "tkinter.messagebox",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="ticketera",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    # No console window for the end user
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # Windows-specific: request user-level execution (no UAC prompt)
    uac_admin=False,
)
