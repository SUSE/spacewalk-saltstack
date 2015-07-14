try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

config = {
    'description': 'Saltwalk',
    'author': 'Duncan Mac-Vicar P.',
    'url': 'https://github.com/SUSE/spacewalk-saltstack.',
    'download_url': 'https://github.com/SUSE/spacewalk-saltstack',
    'author_email': 'dmacvicar@suse.de.',
    'version': '0.1',
    'install_requires': [],
    'packages': ['saltwalk'],
    'scripts': ['bin/saltwalk'],
    'name': 'saltwalk'
}

setup(**config)
