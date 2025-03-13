# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['C:\\Users\\SamuelA\\OneDrive - Paape Companies Inc\\Documents\\2025-01-22- TGML and West Ramp\\file-tree-generator\\src\\file_tree_gui.py'],
    pathex=['C:\\Users\\SamuelA\\OneDrive - Paape Companies Inc\\Documents\\2025-01-22- TGML and West Ramp\\file-tree-generator\\src'],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='file_tree_gui',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['C:\\Users\\SamuelA\\OneDrive - Paape Companies Inc\\Documents\\2025-01-22- TGML and West Ramp\\file-tree-generator\\resources\\icon.ico'],
)
