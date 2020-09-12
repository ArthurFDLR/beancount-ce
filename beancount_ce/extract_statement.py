from pdfminer.high_level import extract_text
from pdfminer.layout import LAParams


def extractTextStatement(pdf_file):
    if pdf_file.split('.')[-1] == 'txt':
        with open(pdf_file, 'r') as f:
            data = f.read()
        return str(data)

    elif pdf_file.split('.')[-1] == 'pdf':
        word_margin = 1.0
        char_margin = 120.0
        line_margin = 0.3
        boxes_flow = 0.5  # LAParams

        # If any LAParams group arguments were passed, create an LAParams object and
        # populate with given args. Otherwise, set it to None.

        laparams = LAParams()
        for param in (
            "word_margin",
            "char_margin",
            "line_margin",
            "boxes_flow",
        ):
            paramv = locals().get(param, None)
            if paramv is not None:
                setattr(laparams, param, paramv)

        text = extract_text(pdf_file=pdf_file, laparams=laparams)
        return text


if __name__ == "__main__":
    import sys

    file_name = ''
    for arg in sys.argv:
        if arg[-4:] == '.pdf':
            file_name = arg

    if len(file_name) > 0:
        print('Extract text from ' + file_name)
        with open(file_name[:-4] + '.txt', 'w', encoding='utf8') as text_file:
            statement = extractTextStatement(str(file_name))
            text_file.write(statement)
    else:
        print('No PDF file found.')
