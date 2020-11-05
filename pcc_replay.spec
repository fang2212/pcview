# -*- mode: python ; coding: utf-8 -*-

block_cipher = None
added_files =[
    ('templates/', 'templates'),
    ('static/', 'static'),
    ('dbc/', 'dbc'),
    ('config/', 'config'),
    ]

a = Analysis(['pcc_replay.py'],
             pathex=['/usr/local/lib/python3.5/dist-packages/cv2/python-3.5'],
             binaries=[],
             datas=added_files,
             hiddenimports=['pkg_resources.py2_warn', 'engineio.async_drivers.eventlet', 'jinja2.ext'],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='pcc_app',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=True )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='pcc_replay')
