__version__ = '0.1.0'

from datetime import datetime
from pdfminer.high_level import extract_text
from pdfminer.layout import LAParams
import regex
from decimal import Decimal as D

from beancount.core import data, flags
from beancount.core.amount import Amount
from beancount.core.number import Decimal
from beancount.ingest import importer

def extractText(pdf_file, outfile='-',
            _py2_no_more_posargs=None,  # Bloody Python2 needs a shim
            no_laparams=False, all_texts=None, detect_vertical=None, # LAParams
            word_margin=None, char_margin=None, line_margin=None, boxes_flow=None, # LAParams
            output_type='text', codec='utf-8', strip_control=False,
            maxpages=0, page_numbers=None, password="", scale=1.0, rotation=0,
            layoutmode='normal', output_dir=None, debug=False,
            disable_caching=False, **other):
    if _py2_no_more_posargs is not None:
        raise ValueError("Too many positional arguments passed.")
    if not pdf_file:
        raise ValueError("Must provide files to work upon!")

    # If any LAParams group arguments were passed, create an LAParams object and
    # populate with given args. Otherwise, set it to None.
    if not no_laparams:
        laparams = LAParams()
        for param in ("all_texts", "detect_vertical", "word_margin", "char_margin", "line_margin", "boxes_flow"):
            paramv = locals().get(param, None)
            if paramv is not None:
                setattr(laparams, param, paramv)
    else:
        laparams = None
    text = extract_text(pdf_file=pdf_file, laparams=laparams)
    return text

def string_to_decimal(strD):
    # replace french separator by english one (otherwise there is a conversion syntax error)
    strD = strD.replace(',', '.')
    # remove useless spaces
    strD = strD.replace(' ', '')
    # convert to decimal
    nb = D(strD)
    return nb


## REGEX FORMATTING ##
######################

# - will match owner
# prior to march 2019
owner_regex_v1 = r'Identifiant client\s+(?P<owner>\D*)'
# after march 2019
owner_regex_v2 = r'^(?P<title>MR|MME|MLLE)\s+(?P<owner>\D*?)$'

# - will match dates
emission_date_regex = r'\b(?P<date>[\d/]{10})\b'

# - will match debits
# Ex 1.
# 18/10 CB CENTRE LECLERC  FACT 161014      13,40
# Ex 2.
# 27/05 PRLV FREE MOBILE      3,99
# -Réf. donneur d'ordre :
# fmpmt-XXXXXXXX
# -Réf. du mandat : FM-XXXXXXXX-X
# [\S\s].*?
debit_regex = (r'^'
    '(?P<op_dte>\d\d\/\d\d)'                                        # date: dd/dd
    '(?P<op_lbl>.*?)'                                               # label: any single character (.), between 0 and unlimited (*), lazy (?)
    '\s.*?'                                                         # any whitespace and non-whitespace character (i.e. any character) ([\S\s]), any character (.) between 0 and unlimited (+), lazy
    '(?P<op_amt>(?<=\s)\d{1,3}\s{1}\d{1,3}\,\d{2}|\d{1,3}\,\d{2}(?!([\S\s].*?((?<=(?=(^(?!(?1))\s.*(?1))))\s.*(?3)))))$'
                                                                    # amount: alternative between ddd ddd,dd and ddd,dd, until the end of line ($)
                                                                    # the positive lookebehind assures that there is at least one white space before any amount
                                                                    # the positive lookbehind handles the following case where amount to match is 4,45 and not 14,40:
                                                                    # 19/10 INTERETS TAEG 14,40
                                                                    # VALEUR AU 18/10     4,45
    '\s*'                                                           # any whitespace character (\s), between 0 and unlimited (*), greedy
    '(?P<op_lbl_extra>[\S\s]*?(?=^(?1)|^(?3)|\Z))'                  # extra label: 'single line mode' until the positive lookehead is satisfied
                                                                    # positive lookahead --> alternative between:
                                                                    #   -line starting with first named subpatern (date)
                                                                    #   -line starting with third named subpatern (amount)
                                                                    #   -EOL
                                                                    # we use [\s\S]*? to do like the single line mode
                                                                    # basically it's going to match any non-whitespace OR whitespace character. That is, any character, including linebreaks.
                                                                    # we could have used (?s) to activate the real line mode...
                                                                    # ...but Python doesn't support mode-modified groups (meaning that it will change the mode for the whole regex)
)

# - will match credits
# Ex 1.
# 150,0008/11 VIREMENT PAR INTERNET
# Ex 2.
# 11,8011/02VIR SEPA LA MUTUELLE DES ETUDIA
# XXXXX/XX/XX-XXXX/XXXXXXXXX
# -Réf. donneur d'ordre :
# XXXXX/XX/XX-XXXX/XXXXXXXXX
credit_regex = (r'^'
    '(?P<op_amt>\d{1,3}\s{1}\d{1,3}\,\d{2}|\d{1,3}\,\d{2})'     # amount: alternative between ddd ddd,dd and ddd,dd
    '(?P<op_dte>\d\d\/\d\d)'                                    # date: dd/dd
    '(?P<op_lbl>.*)$'
    '\s*'                                                       # any whitespace character (\s), between 0 and unlimited (*), greedy
    '(?P<op_lbl_extra>[\S\s]*?(?=^(?1)|^(?2)|\Z))'              # extra label: 'single line mode' until the positive lookehead is satisfied
                                                                # positive lookahead --> alternative between:
                                                                #   -line starting with first subpatern (amount)
                                                                #   -line starting with second subpatern (date)
                                                                #   -EOL
                                                                # we use [\s\S]*? to do like the single line mode
                                                                # basically it's going to match any non-whitespace OR whitespace character. That is, any character, including linebreaks.
                                                                # we could have used (?s) to activate the real line mode...
                                                                # ...but Python doesn't support mode-modified groups (meaning that it will change the mode for the whole regex)
)

# - will match previous account balances (including date and balance)
#   SOLDE PRECEDENT AU 15/10/14 56,05
#   SOLDE PRECEDENT AU 15/10/14 1 575,00
#   SOLDE PRECEDENT   0,00
previous_balance_regex = r'SOLDE PRECEDENT AU (?P<bal_dte>\d\d\/\d\d\/\d\d)\s+(?P<bal_amt>[\d, ]+?)$'

# - will match new account balances
#   NOUVEAU SOLDE CREDITEUR AU 15/11/14 (en francs : 1 026,44) 156,48
new_balance_regex = r'NOUVEAU SOLDE CREDITEUR AU (?P<bal_dte>\d\d\/\d\d\/\d\d)\s+\(en francs : (?P<bal_amt_fr>[\d, ]+)\)\s+(?P<bal_amt>[\d, ]+?)$'

one_character_line_regex = r'^( +|.|\n)$'
longer_than_70_regex = r'^(.{70,})$'
smaller_than_2_regex = r'^.{,2}$'
empty_line_regex = r'^(\s*)$'
trailing_spaces_and_tabs_regex = r'[ \t]+$'
line_return_regex = r'(\n)$'



class CEImporter(importer.ImporterProtocol):
    def __init__(
        self,
        accountNumber: str,
        account: str,
        expenseCat: str = '',
        creditCat:str = '',
        showOperationTypes:bool = False
    ):
        self.accountNumber = accountNumber.replace(' ', '')
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
        text = extractText(file_.name, char_margin = 120.0, word_margin = 1.0, line_margin = 0.3, boxes_flow = 0.5)
        return self._searchEmissionDate(text)
    
    def file_name(self, _):
        return 'CaisseEpargne_Statement.pdf'

    def identify(self, file_) -> bool:
        b = False
        n = file_ if type(file_) == str else file_.name

        if str(n).split('.')[-1].upper() == 'PDF':
            try:
                text = extractText(n, char_margin = 120.0, word_margin = 1.0, line_margin = 0.3, boxes_flow = 0.5)
            except:
                text = ''
            if 'www.caisse-epargne.fr' in text:
                b = True
        return b

    def extract(self, file_, existing_entries=None):
        entries = []

        if not self.identify(file_):
            return []
        
        if type(file_) == str:
            text = extractText(file_, char_margin = 120.0, word_margin = 1.0, line_margin = 0.3, boxes_flow = 0.5)
        else:
            text = extractText(file_.name, char_margin = 120.0, word_margin = 1.0, line_margin = 0.3, boxes_flow = 0.5)
        
        operations = self._getOperations(text)

        for index, op in enumerate(operations):
            isExpense = len(op[6])>0
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

    def _getOperations(self,parsed_statement):
        # Clean-up statement string
        statement = regex.sub(one_character_line_regex, 'FLAG_DELETE_THIS_LINE', parsed_statement, flags=regex.M) # flag lines with one character or less
        statement = '\n'.join([s for s in statement.splitlines() if 'FLAG_DELETE_THIS_LINE' not in s]) # keep only non-flaged lines

        # Get emission date
        emission_date = regex.search(emission_date_regex, statement)
        emission_date = emission_date.group('date').strip()
        emission_date = datetime.strptime(emission_date, '%d/%m/%Y')

        accounts = self._searchAccounts(statement)

        operations = []

        for (full, account_number) in reversed(accounts):
            if account_number == self.accountNumber:

                (statement, _, account) = statement.partition(full)

                # search for last/new balances
                (previous_balance, previous_balance_date) = self._search_previous_balance(account)
                (new_balance, new_balance_date) = self._search_new_balance(account)
                # create total for inconsistency check
                total = D(0.0)

                # clean account to keep only operations
                account = self._clean_account(account, full)
                # search all debit operations
                debit_ops = regex.finditer(debit_regex, account, flags=regex.M)
                for debit_op in debit_ops:
                    debitLine = account[debit_op.start() : debit_op.end()].split('\n')[0]
                    debitLineList = debitLine.split(' ')[1:-1]
                    debitLineCleanList = []
                    for w in debitLineList:
                        if w == 'FACT':
                            break
                        if len(w)>0:
                            debitLineCleanList.append(w)
                    debitLine = ''
                    for i,w in enumerate(debitLineCleanList):
                        debitLine += ('' if i==0 else ' ') + w
                    # extract regex groups
                    op_date = debit_op.group('op_dte').strip()
                    op_label = debit_op.group('op_lbl').strip()
                    op_label_extra = debit_op.group('op_lbl_extra').strip()
                    op_amount = debit_op.group('op_amt').strip()
                    # convert amount to regular Decimal
                    op_amount = string_to_decimal(op_amount)
                    # update total
                    total -= op_amount
                    # print('debit {0}'.format(op_amount))
                    operations.append(self._create_operation_entry(op_date, emission_date,
                                                            full, op_label, debitLine, op_amount, True))

                # search all credit operations
                credit_ops = regex.finditer(credit_regex, account, flags=regex.M)
                for credit_op in credit_ops:
                    # extract regex groups
                    op_date = credit_op.group('op_dte').strip()
                    op_label = credit_op.group('op_lbl').strip()
                    op_label_extra = credit_op.group('op_lbl_extra').strip()
                    op_amount = credit_op.group('op_amt').strip()

                    creditLine = account[credit_op.start() : credit_op.end()].split('\n')[0]
                    creditLine = creditLine[len(op_amount) + len(op_date):]

                    # convert amount to regular Decimal
                    op_amount = string_to_decimal(op_amount)
                    # update total
                    total += op_amount
                    # print('credit {0}'.format(op_amount))

                    operations.append(self._create_operation_entry(op_date, emission_date,
                                                            full, op_label, creditLine, op_amount, False))

                # check inconsistencies
                if not ((previous_balance + total) == new_balance):
                    print(account)
                    print(
                        '⚠️  inconsistency detected between imported operations and new balance')
                    errors += 1
                    print('previous_balance is {0}'.format(previous_balance))
                    print('predicted new_balance is {0}'.format(
                        previous_balance + total))
                    print('new_balance should be {0}'.format(new_balance))
        #print(operations)
        return operations
    
    def _create_operation_entry(self, op_date, statement_emission_date, account_number, op_label,
                                op_label_extra, op_amount, debit):
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
            *(['', '%.2f'%op_amount] if debit else ['%.2f'%op_amount, ''])
        ]
        return op

    def _search_operation_type(self,op_label):
        op_label = op_label.upper()
        # bank fees, international fees, subscription fee to bouquet, etc.
        if ((op_label.startswith('*')) or (op_label.startswith('INTERETS'))):
            opType = 'BANK'
        # cash deposits on the account
        elif ((op_label.startswith('VERSEMENT'))):
            opType = 'DEPOSIT'
        # incoming / outcoming wire transfers: salary, p2p, etc.
        elif ((op_label.startswith('VIREMENT')) or (op_label.startswith('VIR'))):
            opType = 'WIRETRANSFER'
        # check deposits / payments
        elif ((op_label.startswith('CHEQUE')) or (op_label.startswith('REMISE CHEQUES')) or (op_label.startswith('REMISE CHQ'))):
            opType = 'CHECK'
        # payments made via debit card
        elif ((op_label.startswith('CB'))):
            opType = 'CARDDEBIT'
        # withdrawals
        elif ((op_label.startswith('RETRAIT')) or (op_label.startswith('RET DAB'))):
            opType = 'WITHDRAWAL'
        # direct debits
        elif ((op_label.startswith('PRLV'))):
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
    
    def _search_new_balance(self, account):
        new_balance_amount = D(0.0)
        new_balance_date = None
        new_balance = regex.search(new_balance_regex, account, flags=regex.M)

        # if the regex matched
        if new_balance:
            new_balance_date = new_balance.group('bal_dte').strip()
            new_balance_amount = new_balance.group('bal_amt').strip()
            new_balance_amount = string_to_decimal(new_balance_amount)

        if not (new_balance_amount and new_balance_date):
            print('⚠️  couldn\'t find a new balance for this account')
        return (new_balance_amount, new_balance_date)

    def _search_previous_balance(self,account):
        previous_balance_amount = D(0.0)
        previous_balance_date = None
        # in the case of a new account (with no history) or a first statement...
        # ...this regex won't match
        previous_balance = regex.search(previous_balance_regex, account, flags=regex.M)

        # if the regex matched
        if previous_balance:
            previous_balance_date = previous_balance.group('bal_dte').strip()
            previous_balance_amount = previous_balance.group('bal_amt').strip()
            previous_balance_amount = string_to_decimal(previous_balance_amount)

        if not (previous_balance_amount and previous_balance_date):
            print('⚠️  couldn\'t find a previous balance for this account')
        return (previous_balance_amount, previous_balance_date)
    
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
        words_to_remove_regex = r'^.*\b(' + '|'.join(words_to_remove) + r')\b.*$'
        # flag lines longer than 70
        cleaned = regex.sub(longer_than_70_regex, 'FLAG_DELETE_THIS_LINE', cleaned, flags=regex.M)
        # flag lines with words to remove
        cleaned = regex.sub(words_to_remove_regex, 'FLAG_DELETE_THIS_LINE', cleaned, flags=regex.M)
        # remove trailing spaces
        cleaned = regex.sub(trailing_spaces_and_tabs_regex, '', cleaned, flags=regex.M)
        # flag empty lines
        cleaned = regex.sub(empty_line_regex, 'FLAG_DELETE_THIS_LINE', cleaned, flags=regex.M)
        # flag lines with less than 2 characters
        cleaned = regex.sub(smaller_than_2_regex, 'FLAG_DELETE_THIS_LINE', cleaned, flags=regex.M)
        # keep only non-flaged lines
        cleaned = '\n'.join([s for s in cleaned.splitlines() if 'FLAG_DELETE_THIS_LINE' not in s])
        return cleaned

    def _search_account_owner(self, regex_to_use, statement):
        # search for owner to identify multiple accounts
        account_owner = regex.search(regex_to_use, statement, flags=regex.M)
        if (not account_owner):
            raise ValueError('No account owner was found.')
        # extract and strip
        account_owner = account_owner.group('owner').strip()
        return account_owner
    
    def _searchEmissionDate(self,statement):
        emission_date = regex.search(emission_date_regex, statement)
        # extract and strip
        emission_date = emission_date.group('date').strip()
        # parse date
        emission_date = datetime.strptime(
            emission_date, '%d/%m/%Y')
        return emission_date

    def _searchAccounts(self, statement):
        # get owner
        owner = self._search_account_owner(owner_regex_v1, statement)

        account_regex = r'^((?:MR|MME|MLLE) ' + owner + ' - .* - ([^(\n]*))$'
        accounts = regex.findall(account_regex, statement, flags=regex.M)

        # no accounts found, try to get owner with other regex
        if (len(accounts) == 0):
            owner = self._search_account_owner(owner_regex_v2, statement)
            account_regex = r'^((?:MR|MME|MLLE) ' + owner + ' - .* - ([^(\n]*))$'
            accounts = regex.findall(account_regex, statement, flags=regex.M)

        # cleanup account number for each returned account
        # we use a syntax called 'list comprehension'
        cleaned_accounts = [(full, regex.sub(r'\D', '', account_number))
                            for (full, account_number) in accounts]
        return cleaned_accounts