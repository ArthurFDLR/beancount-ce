# Beancount Caisse d'Epargne Importer

[![GitHub](https://img.shields.io/github/license/ArthurFDLR/beancount-ce)](https://github.com/ArthurFDLR/beancount-ce/blob/master/LICENSE)
[![PyPI](https://img.shields.io/pypi/v/beancount-ce)](https://pypi.org/project/beancount-ce/)
![PyPI - Wheel](https://img.shields.io/pypi/wheel/beancount-ce)

`beancount-ce` provides a PDF statements importer for the bank [Caisse d'Epargne](http://www.caisse-epargne.fr) to the [Beancount](http://furius.ca/beancount/) format.

## Installation

```console
    $ pip install beancount-ce
```

## Usage

```python
    CONFIG = [
        CEImporter(
            accountNumber=ACCOUNT_NUMBER,
            account='Assets:FR:CdE:CompteCourant',
            expenseCat='Expenses:FIXME',
            creditCat='Income:FIXME',
            showOperationTypes=False
        ),
    ]
```
