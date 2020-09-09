from setuptools import setup

setup(
    name='beancount-ce',
    version='0.0.1',
    description="Beancount importer for PDF statements from the French bank Caisse d'Epargne",
    url='git@github.com:ArthurFDLR/beancount-ce.git',
    author='Arthur Findelair',
    author_email='arthfind@gmail.com',
    license='MIT',
    packages=['beancount_ce'],
    zip_safe=False,
    install_requires=[
        'beancount>=2.1.3',
        'regex'
    ]
)