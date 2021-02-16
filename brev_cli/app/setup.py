
from setuptools import setup

APP = ['brev.py']
DATA_FILES = []
OPTIONS = {
    'argv_emulation': True,
    'iconfile': 'brev.icns',
    'plist': {
        'CFBundleShortVersionString': '0.2.0',
        'LSUIElement': True,
    },
    'packages': ['rumps', 'env']
    
}

setup(
    app=APP,
    name='brev',
    
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'], install_requires=['rumps']
)
