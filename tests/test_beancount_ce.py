import pathlib
import pytest
import datetime

from beancount_ce import __version__, CEImporter

ACCOUNT_NUMBER_1 = '12345 12345 12345678901'

def test_version():
    assert __version__ == '0.1.0'

@pytest.fixture
def filename():
    return pathlib.Path(__file__).parent.absolute() / 'test_statement.txt'

@pytest.fixture
def importer():
    return CEImporter(ACCOUNT_NUMBER_1, 'Assets:CE')

def test_identify(importer, filename):
    with open(filename) as fd:
        assert importer.identify(fd)

def test_file_date(importer, filename):
    with open(filename) as fd:
        assert importer.file_date(fd) == datetime.date(2020, 5, 16)
