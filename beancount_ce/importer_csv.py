import csv
from datetime import datetime
from typing import Mapping, Tuple

from beancount.core import data
from beancount.core.amount import Amount
from beancount.core.number import Decimal
from beancount.ingest import importer

CSV_DELIMITER = ';'


def get_date(s_date):
    date_patterns = ["%d-%m-%Y", "%Y-%m-%d", "%Y/%m/%d", '%m/%d/%Y']

    for pattern in date_patterns:
        try:
            return datetime.strptime(s_date, pattern).date()
        except:
            pass

    return None


class CEImporter_CSV(importer.ImporterProtocol):
    """Beancount Importer for Caisse d'Epargne CSV statement exports.

    Attributes:
        account (str): Account name in beancount format (e.g. 'Assets:FR:CdE:CompteCourant')
        expenseCat (str, optional): Expense category in beancount format (e.g. 'Expenses:FIXME'). Defaults to '', no expense posting added to the operation.
        creditCat (str, optional): Income category in beancount format (e.g. 'Income:FIXME'). Defaults to '', no income posting added to the operation.
        iban (str, optional): International Bank Account Number of the account you want to extract operations. Note that only the account number is necessary. File will be skipped if account numbers do not match.
    """

    def __init__(
        self,
        account: str,
        expenseCat: str = '',
        creditCat: str = '',
        iban: str = '',
    ):
        self.account = account
        self.expenseCat = expenseCat
        self.creditCat = creditCat
        self.iban = iban

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
            reader = csv.DictReader(
                fd,
                delimiter=CSV_DELIMITER,
                quoting=csv.QUOTE_MINIMAL,
                quotechar='"',
            )
            for line in reader:
                try:
                    date_tmp = get_date(line["Date de comptabilisation"])
                    if date_tmp is None:
                        raise RuntimeError("Wrong date format")
                except Exception as e:
                    print(e)
                    break
                if not date or date_tmp > date:
                    date = date_tmp
        return date

    def file_name(self, _):
        return 'CaisseEpargne_Statement.csv'

    def is_valid_header(self, line: str) -> bool:
        expected_values = set(
            [
                "Date operation",
                "Libelle operation",
                "Libelle simplifie",
                "Debit",
                "Credit",
            ]
        )
        actual_values = set(
            column.strip('\n') for column in line.split(CSV_DELIMITER)
        )
        return expected_values.issubset(actual_values)

    def is_valid_account_number_line(self, line: str) -> bool:
        if not self.iban:
            return True
        try:
            [account_number_key, account_number] = [
                token.strip()
                for token in line.split(CSV_DELIMITER)[0].split(':')
            ]
            return account_number_key == "Numéro de compte" and account_number.replace(
                ' ', ''
            ) in self.iban.replace(
                ' ', ''
            )
        except:
            return False

    def identify(self, file_) -> bool:
        try:
            with open(file_.name) as fd:
                # next(fd)
                # account_number_line = next(fd)
                # next(fd)
                # next(fd)
                header_line = next(fd)
            return self.is_valid_header(
                header_line
            )  # and self.is_valid_account_number_line(account_number_line)
        except:
            return False

    def extract(self, file_, existing_entries=None):
        entries = []

        if not self.identify(file_):
            return []

        with open(file_.name) as fd:
            reader = csv.DictReader(
                fd,
                delimiter=CSV_DELIMITER,
                quoting=csv.QUOTE_MINIMAL,
                quotechar='"',
            )
            for index, line in enumerate(reader):
                meta = data.new_metadata(file_.name, index)
                postings = []
                try:
                    date = get_date(line["Date de comptabilisation"])
                    if date is None:
                        raise RuntimeError("Wrong date format")
                except:
                    break
                amount = (
                    Decimal(line["Debit"].replace(',', '.'))
                    if line["Debit"]
                    else Decimal(line["Credit"].replace(',', '.'))
                )
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
                if amount < 0:
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
                else:
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
                payee = line["Libelle operation"]
                if line["Libelle simplifie"]:
                    payee += f" [{line['Libelle simplifie']}]"
                entries.append(
                    data.Transaction(
                        meta,
                        date,
                        self.FLAG,
                        payee,
                        '',
                        data.EMPTY_SET,
                        data.EMPTY_SET,
                        postings,
                    )
                )
        return entries
