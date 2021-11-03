# -*- mode: python ; coding: utf-8 -*-

block_cipher = None
added_files =[
    ('templates/', 'templates'),
    ('static/', 'static'),
    ('dbc/', 'dbc'),
    ('config/', 'config'),
    ]

a = Analysis(['pcc_replay.py'],
             pathex=['/home/li/code/pcview_new'],
             binaries=[("/home/li/.local/lib/python3.8/site-packages/sharemem/libsharemem.so", "sharemem")],
             datas=added_files,
             hiddenimports=['pkg_resources.py2_warn', 'engineio.async_drivers.eventlet', 'jinja2.ext', 'nnpy', 'aionn', 'websockets.client', 'websockets.server', 'websockets.legacy.auth'],
             hookspath=[],
             hooksconfig={},
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
          name='pcc_replay',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=True,
          disable_windowed_traceback=False,
          target_arch=None,
          codesign_identity=None,
          entitlements_file=None )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas, 
               strip=False,
               upx=True,
               upx_exclude=[],
               name='pcc_replay')
