from datetime import datetime
import regex

from beancount.core import data, flags
from beancount.core.amount import Amount
from beancount.core.number import Decimal
from beancount.ingest import importer

from .extract_statement import extractTextStatement
from .regex_formatter import *


class CEImporter_PDF(importer.ImporterProtocol):
    """Beancount Importer for Caisse d'Epargne PDF statement exports.

    Attributes:
        iban (str): International Bank Account Number of the account you want to extract operations. Note that only the account number is necessary
        account (str): Account name in beancount format (e.g. 'Assets:FR:CdE:CompteCourant')
        expenseCat (str, optional): Expense category in beancount format (e.g. 'Expenses:FIXME'). Defaults to '', no expense posting added to the operation.
        creditCat (str, optional): Income category in beancount format (e.g. 'Income:FIXME'). Defaults to '', no income posting added to the operation.
        showOperationTypes (bool, optional): Show or not operation type (CARDDEBIT, WIRETRANSFER, CHECK ...) in header. Defaults to False.
    """

    def __init__(
        self,
        iban: str,
        account: str,
        expenseCat: str = '',
        creditCat: str = '',
        showOperationTypes: bool = False,
    ):
        self.iban = iban
        self.account = account
        self.expenseCat = expenseCat
        self.creditCat = creditCat
        self.showOperationTypes = showOperationTypes

    ## API Methods ##
    #################

    def name(self):
        return 'CaisseEpargne {}'.format(self.__class__.__name__)

    def file_account(self, _):
        return self.account

    def file_date(self, file_):
        if not self.identify(file_):
            return None
        text = extractTextStatement(file_.name)
        return self._searchEmissionDate(text)

    def file_name(self, _):
        return 'CaisseEpargne_Statement.pdf'

    def identify(self, file_) -> bool:
        b = False
        try:
            text = extractTextStatement(file_.name)
            if 'www.caisse-epargne.fr' in text:
                b = True
        except:
            pass
        return b

    def extract(self, file_, existing_entries=None):
        entries = []

        if not self.identify(file_):
            return []

        if type(file_) == str:
            text = extractTextStatement(file_)
        else:
            text = extractTextStatement(file_.name)

        operations = self._getOperations(text)

        for index, op in enumerate(operations):
            isExpense = len(op[6]) > 0
            if type(file_) == str:
                meta = data.new_metadata(file_, index)
            else:
                meta = data.new_metadata(file_.name, index)

            amount = Decimal(op[6]) if isExpense else Decimal(op[5])
            currency = 'EUR'
            payee = op[4]
            if self.showOperationTypes:
                payee += ' - ' + op[2]
            postings = [
                data.Posting(
                    self.account,
                    Amount((-amount if isExpense else amount), currency),
                    None,
                    None,
                    None,
                    None,
                )
            ]
            if isExpense and len(self.expenseCat) > 0:
                postings.append(
                    data.Posting(
                        self.expenseCat,
                        Amount((amount if isExpense else -amount), currency),
                        None,
                        None,
                        None,
                        None,
                    )
                )

            if not isExpense and len(self.creditCat) > 0:
                postings.append(
                    data.Posting(
                        self.creditCat,
                        Amount((amount if isExpense else -amount), currency),
                        None,
                        None,
                        None,
                        None,
                    )
                )

            entries.append(
                data.Transaction(
                    meta,
                    datetime.strptime(op[0], '%d/%m/%Y').date(),
                    flags.FLAG_OKAY,
                    payee,
                    '',
                    data.EMPTY_SET,
                    data.EMPTY_SET,
                    postings,
                )
            )

        return entries

    ## Utils ##
    ###########

    def _getOperations(self, parsed_statement):
        # Clean-up statement string
        statement = regex.sub(
            one_character_line_regex,
            'FLAG_DELETE_THIS_LINE',
            parsed_statement,
            flags=regex.M,
        )  # flag lines with one character or less
        statement = '\n'.join(
            [
                s
                for s in statement.splitlines()
                if 'FLAG_DELETE_THIS_LINE' not in s
            ]
        )  # keep only non-flaged lines

        # Get emission date
        emission_date = regex.search(emission_date_regex, statement)
        emission_date = emission_date.group('date').strip()
        emission_date = datetime.strptime(emission_date, '%d/%m/%Y')

        accounts = self._searchAccounts(statement)

        operations = []

        for (full, account_number) in reversed(accounts):
            if account_number.replace(' ', '') in self.iban.replace(' ', ''):

                (statement, _, account) = statement.partition(full)

                # create total for inconsistency check
                total = Decimal(0.0)

                # clean account to keep only operations
                account = self._clean_account(account, full)
                # search all debit operations
                debit_ops = regex.finditer(debit_regex, account, flags=regex.M)
                for debit_op in debit_ops:
                    debitLine = account[debit_op.start() : debit_op.end()]
                    debitLine = debitLine.split('\n')[0]
                    debitLineList = debitLine.split(' ')[1:-1]
                    debitLineCleanList = []
                    for w in debitLineList:
                        if w == 'FACT':
                            break
                        if len(w) > 0:
                            debitLineCleanList.append(w)
                    debitLine = ''
                    for i, w in enumerate(debitLineCleanList):
                        debitLine += ('' if i == 0 else ' ') + w
                    # extract regex groups
                    op_date = debit_op.group('op_dte').strip()
                    op_label = debit_op.group('op_lbl').strip()
                    op_label_extra = debit_op.group('op_lbl_extra').strip()
                    op_amount = debit_op.group('op_amt').strip()
                    # convert amount to regular Decimal
                    op_amount = op_amount.replace(',', '.')
                    op_amount = op_amount.replace(' ', '')
                    op_amount = Decimal(op_amount)
                    # update total
                    total -= op_amount
                    # print('debit {0}'.format(op_amount))
                    operations.append(
                        self._create_operation_entry(
                            op_date,
                            emission_date,
                            full,
                            op_label,
                            debitLine,
                            op_amount,
                            True,
                        )
                    )

                # search all credit operations
                credit_ops = regex.finditer(
                    credit_regex, account, flags=regex.M
                )
                for credit_op in credit_ops:
                    # extract regex groups
                    op_date = credit_op.group('op_dte').strip()
                    op_label = credit_op.group('op_lbl').strip()
                    op_label_extra = credit_op.group('op_lbl_extra').strip()
                    op_amount = credit_op.group('op_amt').strip()

                    creditLine = account[credit_op.start() : credit_op.end()]
                    creditLine = creditLine.split('\n')[0]
                    creditLine = creditLine[len(op_amount) + len(op_date) :]

                    # convert amount to regular Decimal
                    op_amount = op_amount.replace(',', '.')
                    op_amount = op_amount.replace(' ', '')
                    op_amount = Decimal(op_amount)
                    # update total
                    total += op_amount
                    # print('credit {0}'.format(op_amount))

                    operations.append(
                        self._create_operation_entry(
                            op_date,
                            emission_date,
                            full,
                            op_label,
                            creditLine,
                            op_amount,
                            False,
                        )
                    )

        return operations

    def _create_operation_entry(
        self,
        op_date,
        statement_emission_date,
        account_number,
        op_label,
        op_label_extra,
        op_amount,
        debit,
    ):
        # search the operation type according to its label
        op_type = self._search_operation_type(op_label)

        op = [
            self._set_operation_year(op_date, statement_emission_date),
            account_number,
            op_type,
            op_label.strip(),
            # op_label_extra.strip().replace('\n','\\'),
            op_label_extra.strip(),
            # the star '*' operator is like spread '...' in JS
            *(['', '%.2f' % op_amount] if debit else ['%.2f' % op_amount, '']),
        ]
        return op

    def _search_operation_type(self, op_label):
        op_label = op_label.upper()
        # bank fees, international fees, subscription fee to bouquet, etc.
        if (op_label.startswith('*')) or (op_label.startswith('INTERETS')):
            opType = 'BANK'
        # cash deposits on the account
        elif op_label.startswith('VERSEMENT'):
            opType = 'DEPOSIT'
        # incoming / outcoming wire transfers: salary, p2p, etc.
        elif (op_label.startswith('VIREMENT')) or (op_label.startswith('VIR')):
            opType = 'WIRETRANSFER'
        # check deposits / payments
        elif (
            (op_label.startswith('CHEQUE'))
            or (op_label.startswith('REMISE CHEQUES'))
            or (op_label.startswith('REMISE CHQ'))
        ):
            opType = 'CHECK'
        # payments made via debit card
        elif op_label.startswith('CB'):
            opType = 'CARDDEBIT'
        # withdrawals
        elif (op_label.startswith('RETRAIT')) or (
            op_label.startswith('RET DAB')
        ):
            opType = 'WITHDRAWAL'
        # direct debits
        elif op_label.startswith('PRLV'):
            opType = 'DIRECTDEBIT'
        else:
            opType = 'OTHER'

        return opType

    def _set_operation_year(self, emission, statement_emission_date):
        # fake a leap year
        emission = datetime.strptime(emission + '00', '%d/%m%y')
        if emission.month <= statement_emission_date.month:
            emission = emission.replace(year=statement_emission_date.year)
        else:
            emission = emission.replace(year=statement_emission_date.year - 1)
        return datetime.strftime(emission, '%d/%m/%Y')

    def _clean_account(self, account, account_number):
        # split the text by the 'new_balance_regex' line
        cleaned = regex.split(new_balance_regex, account, flags=regex.M)
        # keep the first part (i.e. everything that's before the 'new_balance_regex' line)
        cleaned = cleaned[0]
        # flag lines with specific words
        words_to_remove = [
            account_number,
            'Relevé',
            'vos comptes',
            'Page',
            'Débit Crédit',
            'Détail des opérations',
            'frais bancaires et cotisations',
            'SOLDE PRECEDENT AU',
        ]
        words_to_remove_regex = (
            r'^.*\b(' + '|'.join(words_to_remove) + r')\b.*$'
        )
        # flag lines longer than 70
        cleaned = regex.sub(
            longer_than_70_regex,
            'FLAG_DELETE_THIS_LINE',
            cleaned,
            flags=regex.M,
        )
        # flag lines with words to remove
        cleaned = regex.sub(
            words_to_remove_regex,
            'FLAG_DELETE_THIS_LINE',
            cleaned,
            flags=regex.M,
        )
        # remove trailing spaces
        cleaned = regex.sub(
            trailing_spaces_and_tabs_regex, '', cleaned, flags=regex.M
        )
        # flag empty lines
        cleaned = regex.sub(
            empty_line_regex, 'FLAG_DELETE_THIS_LINE', cleaned, flags=regex.M
        )
        # flag lines with less than 2 characters
        cleaned = regex.sub(
            smaller_than_2_regex,
            'FLAG_DELETE_THIS_LINE',
            cleaned,
            flags=regex.M,
        )
        # keep only non-flaged lines
        cleaned = '\n'.join(
            [
                s
                for s in cleaned.splitlines()
                if 'FLAG_DELETE_THIS_LINE' not in s
            ]
        )
        return cleaned

    def _search_account_owner(self, regex_to_use, statement):
        # search for owner to identify multiple accounts
        account_owner = regex.search(regex_to_use, statement, flags=regex.M)
        if not account_owner:
            raise ValueError('No account owner was found.')
        # extract and strip
        account_owner = account_owner.group('owner').strip()
        return account_owner

    def _searchEmissionDate(self, statement):
        emission_date = regex.search(emission_date_regex, statement)
        # extract and strip
        emission_date = emission_date.group('date').strip()
        # parse date
        emission_date = datetime.strptime(emission_date, '%d/%m/%Y')
        return emission_date.date()

    def _searchAccounts(self, statement):
        # get owner
        owner = self._search_account_owner(owner_regex_v1, statement)

        account_regex = r'^((?:MR|MME|MLLE) ' + owner + ' - .* - ([^(\n]*))$'
        accounts = regex.findall(account_regex, statement, flags=regex.M)

        # no accounts found, try to get owner with other regex
        if len(accounts) == 0:
            owner = self._search_account_owner(owner_regex_v2, statement)
            account_regex = (
                r'^((?:MR|MME|MLLE) ' + owner + ' - .* - ([^(\n]*))$'
            )
            accounts = regex.findall(account_regex, statement, flags=regex.M)

        # cleanup account number for each returned account
        # we use a syntax called 'list comprehension'
        cleaned_accounts = [
            (full, regex.sub(r'\D', '', account_number))
            for (full, account_number) in accounts
        ]
        return cleaned_accounts
