import os
from setuptools import setup

with open('README.md', 'r') as fh:
    long_description = fh.read()

setup(
    name='beancount-ce',
    version='0.1',
    description="Beancount importer for PDF statements from the French bank Caisse d'Epargne",
    long_description=long_description,
    long_description_content_type='text/markdown',
    #url='git@github.com:ArthurFDLR/beancount-ce.git',
    url='https://github.com/ArthurFDLR/beancount-ce',
    download_url='https://github.com/ArthurFDLR/beancount-ce/archive/v0.1.tar.gz',
    author='Arthur Findelair',
    author_email='arthfind@gmail.com',
    license='MIT',
    packages=['beancount_ce'],
    zip_safe=False,
    install_requires=['regex~=2020.7.14', 'beancount>=2.1.3', 'pdfminer.six']
)