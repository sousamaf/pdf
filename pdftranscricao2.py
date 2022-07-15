import os
import click
from sys import platform
from PyPDF2 import PdfMerger
from PyPDF2 import PdfReader
from PyPDF2 import PdfWriter
from dotenv import load_dotenv
from rich.console import Console

'''
    Como gerar o executável:
    pyinstaller --onefile pdftranscricao.py


    update using: https://pypdf2.readthedocs.io/en/latest/user/merging-pdfs.html
'''

home = os.environ.get("HOME")
load_dotenv(dotenv_path=os.path.join(home, ".env"))

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])

def check_if_exists(filename):
    if os.path.exists(filename):
        return True
    return False


def pdf_merger(filesname, output):
    merger = PdfMerger()

    for pdf in filesname:
        if check_if_exists(pdf):
            merger.append(pdf)
        else:
            console.log("[red]O arquivo {} não existe.[/red]".format(pdf))
    if len(merger.pages):
        merger.write(output)
    else:
        console.log("\n[red]***Nenhm arquivo de saída foi criado.***[/red]\n".format(pdf))
    merger.close()


def pdf_compresser(filename, output):
    if check_if_exists(filename):
        reader = PdfReader(filename)
        writer = PdfWriter()

        for page in reader.pages:
            page.compress_content_streams()
            writer.add_page(page)
        
        with open(output, "wb") as f:
            writer.write(f)
    else:
        console.log("[red]O arquivo {} não existe.[/red]".format(filename))

@click.group(context_settings=CONTEXT_SETTINGS)
@click.version_option(version='0.3.0')
def pdf():
    pass

@pdf.command()
@click.argument('filename')
@click.option("-o", type=str, default="compressed.pdf")
def compress(filename, o):
    """Realiza a compactação de um arquivo PDF."""
    pdf_compresser(filename, o)


@pdf.command()
@click.argument('filename', type=str, nargs=-1)
@click.option("-o", type=str, default="merged.pdf")
def merger(filename, o):
    """Realiza a junção de arquivos PDF."""
    pdf_merger(filename, o)


if __name__ == '__main__':
    console = Console()
    pdf()