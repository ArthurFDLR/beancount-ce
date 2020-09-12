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
    IBAN_NUMBER_CE = 'FR00 1111 2222 3333 4444 5555 666'

    CONFIG = [
        CEImporter(
            iban=IBAN_NUMBER_CE,
            account='Assets:FR:CdE:CompteCourant',
            expenseCat='Expenses:FIXME',    #Optional
            creditCat='Income:FIXME',       #Optional
            showOperationTypes=False        #Optional
        ),
    ]
```
