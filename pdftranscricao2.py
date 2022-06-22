import os
import click
from sys import platform
from PyPDF2 import PdfMerger
from PyPDF2 import PdfReader
from PyPDF2 import PdfWriter
from dotenv import load_dotenv

'''
    Como gerar o executável:
    pyinstaller --onefile pdftranscricao.py


    update using: https://pypdf2.readthedocs.io/en/latest/user/merging-pdfs.html
'''

home = os.environ.get("HOME")
load_dotenv(dotenv_path=os.path.join(home, ".env"))

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


def pdf_merger(filesname):
    print(filesname)
    exit(0)
    merger = PdfMerger()

    for pdf in filesname:
        merger.append(pdf)
    merger.write("merged.pdf")
    merger.close()


def pdf_compresser(filename):
    reader = PdfReader(filename)
    writer = PdfWriter()

    for page in reader.pages:
        page.compress_content_streams()
        writer.add_page(page)
    
    with open("compressed.pdf", "wb") as f:
        writer.write(f)


@click.group(context_settings=CONTEXT_SETTINGS)
@click.version_option(version='0.3.0')
def pdf():
    pass

@pdf.command()
@click.argument('filename')
def compress(filename):
    """Realiza a compactação de um arquivo PDF."""
    pdf_compresser(filename)


@pdf.command()
# @click.argument('filesname')
@click.option("--f", multiple=True, type=str)
def merger(f):
    """Realiza a junção de arquivos PDF."""
    pdf_merger(f)


if __name__ == '__main__':
    pdf()