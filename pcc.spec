# -*- mode: python ; coding: utf-8 -*-

block_cipher = None
added_files = [
	('config', 'config'), 
	('dbc', 'dbc'),
	('nanomsg', 'nanomsg'),
	('_nanomsg_cpy', '_nanomsg_cpy'),
	('web', 'web')
]

a = Analysis(['pcc.py'],
             pathex=['.'],
             binaries=[],
             datas= added_files,
             hiddenimports=['kiwisolver', 'tkinter', 'matplotlib', 'nanomsg'],
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
          name='pcc',
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
               name='pcc', icon='collection.ico')
