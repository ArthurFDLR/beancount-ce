import csv
from datetime import datetime
from typing import Mapping, Tuple

from beancount.core import data
from beancount.core.amount import Amount
from beancount.core.number import Decimal
from beancount.ingest import importer


class CEImporter_CSV(importer.ImporterProtocol):
    """ Beancount Importer for Caisse d'Epargne CSV statement exports.

    Attributes:
        account (str): Account name in beancount format (e.g. 'Assets:FR:CdE:CompteCourant')
        expenseCat (str, optional): Expense category in beancount format (e.g. 'Expenses:FIXME'). Defaults to '', no expense posting added to the operation.
        creditCat (str, optional): Income category in beancount format (e.g. 'Income:FIXME'). Defaults to '', no income posting added to the operation.
    """

    def __init__(
        self, account: str, expenseCat: str = '', creditCat: str = '',
    ):
        self.account = account
        self.expenseCat = expenseCat
        self.creditCat = creditCat

    ## API Methods ##
    #################

    def name(self):
        return 'Caisse Epargne: {}'.format(self.__class__.__name__)

    def file_account(self, _):
        return self.account

    def file_date(self, file_):
        if not self.identify(file_):
            return None
        date = None
        with open(file_.name) as fd:
            for _ in range(4):
                next(fd)
            reader = csv.DictReader(
                fd, delimiter=';', quoting=csv.QUOTE_MINIMAL, quotechar='"'
            )
            for line in reader:
                try:
                    date_tmp = datetime.strptime(
                        line["Date"], '%d/%m/%y'
                    ).date()
                except:
                    break
                if not date or date_tmp > date:
                    date = date_tmp
        return date

    def file_name(self, _):
        return 'CaisseEpargne_Statement.csv'

    def is_valid_header(self, line: str) -> bool:
        expected_values = [
            "Date",
            "Numéro d'opération",
            "Libellé",
            "Débit",
            "Crédit",
            "Détail",
        ]
        actual_values = [column.strip('"') for column in line.split(';')]
        for (expected, actual) in zip(expected_values, actual_values):
            if expected != actual:
                return False
        return True

    def identify(self, file_) -> bool:
        try:
            with open(file_.name) as fd:
                for _ in range(5):
                    line = next(fd)
            return self.is_valid_header(line)
        except:
            return False

    def extract(self, file_, existing_entries=None):
        entries = []

        if not self.identify(file_):
            return []

        with open(file_.name) as fd:
            for _ in range(4):
                next(fd)
            reader = csv.DictReader(
                fd, delimiter=';', quoting=csv.QUOTE_MINIMAL, quotechar='"'
            )

            for index, line in enumerate(reader):
                meta = data.new_metadata(file_.name, index)
                postings = []
                try:
                    date = datetime.strptime(line["Date"], '%d/%m/%y').date()
                except:
                    break
                if len(line["Débit"]) > 0:
                    amount = Decimal(line["Débit"].replace(',', '.'))
                    postings.append(
                        data.Posting(
                            self.account,
                            Amount(amount, 'EUR'),
                            None,
                            None,
                            None,
                            None,
                        )
                    )
                    if len(self.expenseCat) > 0:
                        postings.append(
                            data.Posting(
                                self.expenseCat,
                                Amount(-amount, 'EUR'),
                                None,
                                None,
                                None,
                                None,
                            )
                        )

                if len(line["Crédit"]) > 0:
                    amount = Decimal(line["Crédit"].replace(',', '.'))
                    postings.append(
                        data.Posting(
                            self.account,
                            Amount(amount, 'EUR'),
                            None,
                            None,
                            None,
                            None,
                        )
                    )
                    if len(self.creditCat) > 0:
                        postings.append(
                            data.Posting(
                                self.creditCat,
                                Amount(-amount, 'EUR'),
                                None,
                                None,
                                None,
                                None,
                            )
                        )

                entries.append(
                    data.Transaction(
                        meta,
                        date,
                        self.FLAG,
                        line["Libellé"],
                        '',
                        data.EMPTY_SET,
                        data.EMPTY_SET,
                        postings,
                    )
                )

        return entries
