# Beancount Caisse d'Epargne Importer

![GitHub](https://img.shields.io/github/license/ArthurFDLR/beancount-ce)


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
