# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_data_files, collect_all

block_cipher = None

# Tratament special pentru librăriile complexe care nu funcționează arhivate
datas_sb, binaries_sb, hiddenimports_sb = collect_all('speechbrain')
datas_grpc, binaries_grpc, hiddenimports_grpc = collect_all('grpc')

# Metoda standard pentru restul
datas = []
datas += collect_data_files('speech_recognition')
datas += collect_data_files('pygame')

# Resursele aplicației
app_datas = [
    ('assets', 'assets'),
    ('characters', 'characters'),
    ('curriculum', 'curriculum'),
    ('scenes', 'scenes'),
    ('Backgrounds', 'Backgrounds'),
]

a = Analysis(
    ['main_app.py'],
    pathex=[],
    binaries=binaries_sb + binaries_grpc,
    datas=datas + datas_sb + datas_grpc + app_datas,
    hiddenimports=[
        'pygame', 
        'sounddevice',
        'soundfile',
        'speechbrain.inference',
        'edge_tts',
        'google.generativeai',
        'PIL',
        'numpy',
        'cv2',
    ] + hiddenimports_sb + hiddenimports_grpc,
    hookspath=[],
    runtime_hooks=[], # Nu mai avem nevoie de hook-ul extern
    hooksconfig={},
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
    [],
    exclude_binaries=True,
    name='TeatruDigital',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/ui/icon.ico',
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='TeatruDigital',
)