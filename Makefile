# build & publish

build:
	poetry build

publish-pip:
	poetry publish


# formatting

fmt-black:
	poetry run black beancount_ce/ tests/

# lint

lint:
	poetry run black --check beancount_ce/ tests/

# test

pdf_to_txt:
ifdef file
		poetry run python beancount_ce/extract_statement.py $(file)
else
		@echo PDF Statement needed, try:
		@echo     make pdf_to_txt file="url/to/pdf_statement.pdf"
endif

test:
	poetry run pytest tests/
