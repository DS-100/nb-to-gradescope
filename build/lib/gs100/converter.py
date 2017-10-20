"""
Converts a notebook with student written answers to a PDF for Gradescope.
Ensures that each question has a constant number of pages.
"""
__all__ = ['convert']

from bs4 import BeautifulSoup
from nbconvert import HTMLExporter
from toolz.curried import first, filter
import logging
import nbformat
import os
import pdfkit
import PyPDF2
import subprocess
import sys
import time

# Default number of pages per question
DEFAULT_PAGES_PER_Q = 2

# Tags on cells that need to get exported
TAGS = ['written', 'student']

WKHTMLTOPDF_URL = 'https://github.com/JazzCore/python-pdfkit/wiki/Installing-wkhtmltopdf'  # noqa: E501


def convert(filename, num_questions=None, pages_per_q=DEFAULT_PAGES_PER_Q,
            folder='question_pdfs', output='gradescope.pdf'):
    """
    Public method that exports nb to PDF and pads all the questions.

    If num_questions is specified, will also check the final PDF for missing
    questions.
    """
    check_for_wkhtmltohtml()
    save_notebook(filename)

    nb = read_nb(filename)
    pdf_names = create_question_pdfs(nb, pages_per_q=pages_per_q,
                                     folder=folder)
    merge_pdfs(pdf_names, output)

    if num_questions is not None and len(pdf_names) != num_questions:
        logging.warning(
            'We expected there to be {} questions but there are only {} in '
            'your final PDF. Gradescope will most likely not accept your '
            'submission. Double check that you wrote your answers in the '
            'cells that we provided.'
            .format(num_questions, len(pdf_names))
        )

    print('Done! The resulting PDF is located in this directory and is called '
          '{}. Upload that PDF to Gradescope for grading.'.format(output))


##############################################################################
# Private methods
##############################################################################

def check_for_wkhtmltohtml():
    """
    Checks to see if the wkhtmltohtml binary is installed. Raises error if not.
    """
    locator = 'where' if sys.platform == 'win32' else 'which'

    wkhtmltopdf = (subprocess.Popen([locator, 'wkhtmltopdf'],
                                    stdout=subprocess.PIPE)
                   .communicate()[0].strip())

    if not os.path.exists(wkhtmltopdf):
        logging.error(
            'No wkhtmltopdf executable found. Please install '
            'wkhtmltopdf before trying again - {}'.format(WKHTMLTOPDF_URL))
        raise ValueError(
            'No wkhtmltopdf executable found. Please install '
            'wkhtmltopdf before trying again - {}'.format(WKHTMLTOPDF_URL))


# This function is stolen from ok-client
def save_notebook(filename):
    try:
        from IPython.display import display, Javascript
    except ImportError:
        logging.warning("Could not import IPython Display Function")
        print("Make sure to save your notebook before sending it to OK!")
        return

    display(Javascript('IPython.notebook.save_checkpoint();'))
    display(Javascript('IPython.notebook.save_notebook();'))
    print('Saving notebook...', end=' ')

    if wait_for_save(filename):
        print("Saved '{}'.".format(filename))
    else:
        logging.warning("Timed out waiting for IPython save")
        print("Could not save your notebook. Make sure your notebook"
              " is saved before exporting!")


def wait_for_save(filename, timeout=5):
    """Waits for FILENAME to update, waiting up to TIMEOUT seconds.
    Returns True if a save was detected, and False otherwise.
    """
    modification_time = os.path.getmtime(filename)
    start_time = time.time()
    while time.time() < start_time + timeout:
        if (os.path.getmtime(filename) > modification_time
                and os.path.getsize(filename) > 0):
            return True
        time.sleep(0.2)
    return False


def cell_has_tags(cell) -> bool:
    return ('tags' in cell.metadata
            and all(tag in cell.metadata.tags for tag in TAGS))


def remove_input(cell) -> nbformat.NotebookNode:
    cell.source = 'output:'
    return cell


def read_nb(filename) -> nbformat.NotebookNode:
    """
    Takes in a filename of a notebook and returns a notebook object containing
    only the cell outputs to export.
    """
    with open(filename, 'r') as f:
        nb = nbformat.read(f, as_version=4)

    cells = [remove_input(cell) for cell in nb['cells']
             if cell_has_tags(cell)]

    nb['cells'] = cells
    return nb


def nb_to_html_cells(nb) -> list:
    """
    Converts notebook to an iterable of BS4 HTML nodes. Images are inline.
    """
    html_exporter = HTMLExporter()
    html_exporter.template_file = 'basic'

    (body, resources) = html_exporter.from_notebook_node(nb)
    return BeautifulSoup(body, 'html.parser').findAll('div', class_='cell')


def nb_to_q_nums(nb) -> list:
    """
    Gets question numbers from each cell in the notebook
    """
    def q_num(cell):
        assert cell.metadata.tags
        return first(filter(lambda t: 'q' in t, cell.metadata.tags))

    return [q_num(cell) for cell in nb['cells']]


def pad_pdf_pages(pdf_name, pages_per_q) -> None:
    """
    Checks if PDF has the correct number of pages. If it has too many, warns
    the user. If it has too few, adds blank pages until the right length is
    reached.
    """
    pdf = PyPDF2.PdfFileReader(pdf_name)
    output = PyPDF2.PdfFileWriter()
    num_pages = pdf.getNumPages()
    if num_pages > pages_per_q:
        logging.warning('{} has {} pages. Only the first '
                        '{} pages will get output.'
                        .format(pdf_name, num_pages, pages_per_q))

    # Copy over up to pages_per_q pages
    for page in range(min(num_pages, pages_per_q)):
        output.addPage(pdf.getPage(page))

    # Pad if necessary
    if num_pages < pages_per_q:
        for page in range(pages_per_q - num_pages):
            output.addBlankPage()

    # Output the PDF
    with open(pdf_name, 'wb') as out_file:
        output.write(out_file)


# Options to pass into pdfkit
PDF_OPTS = {
    'page-size': 'Letter',
    'margin-top': '0.25in',
    'margin-right': '0.25in',
    'margin-bottom': '0.25in',
    'margin-left': '0.25in',
    'encoding': "UTF-8",

    'zoom': 4,

    'quiet': '',
}


def create_question_pdfs(nb, pages_per_q, folder) -> list:
    """
    Converts each cells in tbe notebook to a PDF named something like
    'q04c.pdf'. Places PDFs in the specified folder and returns the list of
    created PDF locations.
    """
    html_cells = nb_to_html_cells(nb)
    q_nums = nb_to_q_nums(nb)

    os.makedirs(folder, exist_ok=True)

    pdf_names = []
    for question, cell in zip(q_nums, html_cells):
        # Create question PDFs
        pdf_name = os.path.join(folder, '{}.pdf'.format(question))

        pdfkit.from_string(cell.prettify(), pdf_name, options=PDF_OPTS)

        pad_pdf_pages(pdf_name, pages_per_q)

        print('Created ' + pdf_name)
        pdf_names.append(pdf_name)
    return pdf_names


def merge_pdfs(pdf_names, output) -> None:
    """
    Merges all pdfs together into a single long PDF.
    """
    merger = PyPDF2.PdfFileMerger()

    for filename in pdf_names:
        merger.append(filename)
    merger.write(output)
    merger.close()
