# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['..\\..\\main.py'],
    pathex=[],
    binaries=[],
    datas=[('C:\\divan_api_tester\\styles', 'styles'), ('C:\\divan_api_tester\\image', 'image'), ('C:\\divan_api_tester\\config.json', '.'), ('C:\\divan_api_tester\\mod\\reports\\data\\menu_catalog.json', 'mod\\reports\\data')],
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
    [],
    exclude_binaries=True,
    name='LegoReport',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='LegoReport',
)
