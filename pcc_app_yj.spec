# -*- mode: python ; coding: utf-8 -*-

block_cipher = None
added_files =[
    ('templates', 'templates'),
    ('static', 'static'),
    ('config', 'config'),
    ('dbc', 'dbc')
    ]

a = Analysis(['pcc_app.py'],
             pathex=['./'],
             binaries=[],
             datas= added_files,
             hiddenimports=['_nanomsg_cpy', 'pkg_resources.py2_warn', 'engineio.async_drivers.eventlet', 'jinja2.ext'],
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
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='pcc',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=True )
