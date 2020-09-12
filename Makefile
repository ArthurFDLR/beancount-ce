# build & publish

build:
	poetry build

publish-pip:
	poetry publish


# formatting

fmt-black:
	poetry run black beancount_n26/ tests/

# lint

lint-black:
	poetry run black --check beancount_n26/ tests/

lint-flake8:
	poetry run flake8 beancount_n26/ tests/

lint: lint-black lint-flake8

# test

pdf_to_txt:
ifdef file
		poetry run python beancount_ce/extract_statement.py $(file)
else
		@echo PDF Statement needed, try:
		@echo     make pdf_to_txt file="url/to/pdf_statement.pdf"
endif

test-pytest:
	poetry run pytest tests/

test: test-pytest
