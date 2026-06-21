# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('resources', 'resources'), # Ётой строки достаточно, она скопирует ¬—ё папку целиком
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

# Ѕлок EXE теперь собирает “ќЋ№ ќ скрипты (без внутренних datas и binaries)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True, # ќб€зательный флаг дл€ сборки в режиме папки!
    name='IlyushaGrate',
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
    icon=['resources\\icon.ico'],
)

# ƒќЅј¬Ћя≈ћ ЅЋќ  COLLECT Ч именно он создаст папку dist и положит туда resources
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='IlyushaGrate', # »м€ финальной папки внутри dist
)