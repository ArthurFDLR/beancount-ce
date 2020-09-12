import pathlib
import pytest
import datetime

from beancount_ce import __version__, CEImporter
from beancount.core.number import Decimal

TEST_FILE_PATH = 'test_statement.txt'

TEST_ACCOUNT_NUMBER = 'FR76 1234 5123 4512 3456 7890 130'
TEST_DATE = datetime.date(2020, 5, 16)

def test_version():
    assert __version__ == '0.1.0'

@pytest.fixture
def filename():
    return pathlib.Path(__file__).parent.absolute() / TEST_FILE_PATH

@pytest.fixture
def importer():
    return CEImporter(TEST_ACCOUNT_NUMBER, 'Assets:CE')

def test_identify(importer, filename):
    with open(filename) as fd:
        assert importer.identify(fd)

def test_file_date(importer, filename):
    with open(filename) as fd:
        assert importer.file_date(fd) == TEST_DATE

def test_extract(importer, filename):
    with open(filename) as fd:
        operations = importer.extract(fd)

    operations_test = [
        {'date':datetime.date(2020, 4, 17), 'amount':Decimal('-14.90'), 'payee':'* OP DEBIT BANQUE'},
        {'date':datetime.date(2020, 4, 17), 'amount':Decimal('4.40'), 'payee':'* OP CREDIT BANQUE'},
        {'date':datetime.date(2020, 4, 20), 'amount':Decimal('24.00'), 'payee':'VIR SEPA ENTRANT'},
        {'date':datetime.date(2020, 4, 21), 'amount':Decimal('-63.43'), 'payee':'CB ACHAT 1'},
        {'date':datetime.date(2020, 4, 22), 'amount':Decimal('-63.11'), 'payee':'CB ACHAT 2'},
        {'date':datetime.date(2020, 4, 27), 'amount':Decimal('-20.00'), 'payee':'PRLV Prlvt 1'},
        {'date':datetime.date(2020, 5, 15), 'amount':Decimal('-7.32'), 'payee':'CB ACHAT 3'},
        ]
    op_name_test = [op_test['payee'] for op_test in operations_test]

    assert len(operations) == len(operations_test), 'Wrong number of operations extracted'

    for op in operations:

        assert op.payee in op_name_test, 'Missing operation'
        op_test = operations_test[op_name_test.index(op.payee)]

        assert op.payee == op_test['payee'], 'Wrong payee name'
        assert op.date == op_test['date'], 'Wrong date'

        assert len(op.postings) == 1
        assert op.postings[0].account == 'Assets:CE', 'Wrong account name'
        assert op.postings[0].units.currency == 'EUR', 'Wrong currency'
        assert op.postings[0].units.number == op_test['amount'],  'Wrong amount'

