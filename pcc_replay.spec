# -*- mode: python ; coding: utf-8 -*-

block_cipher = None
added_files = [
	('/home/nan/workshop/git/pcview/config', 'config'), 
	('/home/nan/workshop/git/pcview/dbc', 'dbc'),
	('/home/nan/Desktop/nanomsg/nanomsg', 'nanomsg'),
	('/home/nan/Desktop/nanomsg/_nanomsg_cpy', '_nanomsg_cpy')
]

a = Analysis(['/home/nan/workshop/git/pcview/pcc_replay.py'],
             pathex=['.'],
             binaries=[('/home/nan/workshop/git/nanomsg/build/libnanomsg.so', '.')],
             datas= added_files,
             hiddenimports=[],
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
          name='pcc_replay',
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
               name='pcc_replay', icon='collection.ico')
