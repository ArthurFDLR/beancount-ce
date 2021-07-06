# Beancount Caisse d'Epargne Importer

[![GitHub Workflow Status](https://img.shields.io/github/workflow/status/ArthurFDLR/beancount-ce/beancount-ce?style=for-the-badge)](https://github.com/ArthurFDLR/beancount-ce/actions)
[![PyPI](https://img.shields.io/pypi/v/beancount-ce?style=for-the-badge)](https://pypi.org/project/beancount-ce/)
[![PyPI - Version](https://img.shields.io/pypi/pyversions/beancount-ce.svg?style=for-the-badge)](https://pypi.org/project/beancount-ce/)
[![GitHub](https://img.shields.io/github/license/ArthurFDLR/beancount-ce?style=for-the-badge)](https://github.com/ArthurFDLR/beancount-ce/blob/master/LICENSE.txt)
[![Linting](https://img.shields.io/badge/code%20style-black-000000.svg?style=for-the-badge)](https://github.com/psf/black)

`beancount-ce` provides a statements (PDF and CSV) importer for the bank [Caisse d'Epargne](http://www.caisse-epargne.fr) to the [Beancount](http://furius.ca/beancount/) format.

## Installation

```console
    $ pip install beancount-ce
```

## Usage

Add ```CEImporter``` to your [Beancount importers config file](https://beancount.github.io/docs/importing_external_data.html#configuration).

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

## Contribution

Feel free to contribute!

Please make sure you have Python 3.6+ and [`Poetry`](https://poetry.eustace.io/) installed.

1. Git clone the repository - `git clone https://github.com/ArthurFDLR/beancount-ce`

2. Install the packages required for development - `poetry install`

3. That's basically it. You should now be able to run lint checks and the test suite - `make lint test`.
