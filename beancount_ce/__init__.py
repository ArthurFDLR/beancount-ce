__version__ = '1.0.7'

from .importer_csv import CEImporter_CSV
from .importer_pdf import CEImporter_PDF

from beancount.ingest import importer


class CEImporter(importer.ImporterProtocol):
    """Beancount Importer for Caisse d'Epargne PDF and CSV statement.

    Attributes:
        iban (str): International Bank Account Number of the account you want to extract operations. Note that only the account number is necessary.
        account (str): Account name in beancount format (e.g. 'Assets:FR:CdE:CompteCourant')
        file_type (int): Define file type treated by this importer instance: 0 -> PDF and CSV, 1 -> only PDF, 2 -> only CSV. Defaults to PDF and CSV.
        expenseCat (str, optional): Expense category in beancount format (e.g. 'Expenses:FIXME'). Defaults to '', no expense posting added to the operation.
        creditCat (str, optional): Income category in beancount format (e.g. 'Income:FIXME'). Defaults to '', no income posting added to the operation.
        showOperationTypes (bool, optional): Show or not operation type (CARDDEBIT, WIRETRANSFER, CHECK ...) in header. Only possible for PDF statements. Defaults to False.
    """

    def __init__(
        self,
        iban: str,
        account: str,
        file_type: int = 0,
        expenseCat: str = '',
        creditCat: str = '',
        showOperationTypes: bool = False,
    ):
        self.iban = iban
        self.account = account
        self.expenseCat = expenseCat
        self.creditCat = creditCat
        self.showOperationTypes = showOperationTypes
        self.file_type = file_type

        assert self.file_type in [0, 1, 2]
        if self.file_type in [0, 2]:
            self.csv_importer = CEImporter_CSV(
                account=self.account,
                expenseCat=self.expenseCat,
                creditCat=self.creditCat,
                iban=self.iban,
            )
        if self.file_type in [0, 1]:
            self.pdf_importer = CEImporter_PDF(
                iban=self.iban,
                account=self.account,
                expenseCat=self.expenseCat,
                creditCat=self.creditCat,
                showOperationTypes=self.showOperationTypes,
            )

    def _get_importer(self, file_):
        ext_str = file_.name.split('.')[-1].lower()
        if self.file_type == 0:
            if self.pdf_importer.identify(file_):
                return self.pdf_importer
            if self.csv_importer.identify(file_):
                return self.csv_importer
        if (self.file_type == 1) and self.pdf_importer.identify(file_):
            return self.pdf_importer
        if (self.file_type == 2) and self.csv_importer.identify(file_):
            return self.csv_importer
        return None

    ## API Methods ##
    #################

    def name(self):
        return 'Caisse Epargne: {}'.format(self.__class__.__name__)

    def file_account(self, file_):
        importer = self._get_importer(file_)
        return importer.file_account(file_) if importer else None

    def file_date(self, file_):
        importer = self._get_importer(file_)
        return importer.file_date(file_) if importer else None

    def file_name(self, file_):
        importer = self._get_importer(file_)
        return importer.file_name(file_) if importer else None

    def identify(self, file_) -> bool:
        if self.file_type == 0:
            return self.pdf_importer.identify(
                file_
            ) or self.csv_importer.identify(file_)
        if self.file_type == 1:
            return self.pdf_importer.identify(file_)
        if self.file_type == 2:
            return self.csv_importer.identify(file_)
        return False

    def extract(self, file_, existing_entries=None):
        importer = self._get_importer(file_)
        return importer.extract(file_, existing_entries) if importer else None
