import os
import shutil
import argparse
import tempfile
import subprocess
from dotenv import load_dotenv
from pdftools import pdf_merge
from pdfcompress import compress
from pdfpageinfo import resize2A2
from webdav3.client import Client
from PyPDF2 import PdfFileReader, PdfFileMerger

from rich.panel import Panel
from rich.console import Console
from rich.progress import Progress
console = Console()
load_dotenv()

def pdf_details_update( file_input, 
                        author = "", 
                        title = "",
                        subtitle = ""
                    ):
    file_in = open(file_input, 'rb')
    pdf_reader = PdfFileReader(file_in)
    metadata = pdf_reader.getDocumentInfo()
    # pprint.pprint(metadata)

    pdf_meta_merger = PdfFileMerger()
    pdf_meta_merger.append(file_in)
    pdf_meta_merger.addMetadata({
        '/Author': author,
        '/Title': title,
        '/Subtitle' : subtitle,
    })
    file_out = open("new_{}".format(file_input), 'wb')
    pdf_meta_merger.write(file_out)

    file_in.close()
    file_out.close()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--livro", "-L", help="Código do livro. Por exemplo: 3-G.", type=str, required=True)
    parser.add_argument("--pagina", "-P", help="Página do livro.", type=str, required=True)
    parser.add_argument("--termoinicial", "-TI", help="Primeiro Termo completo na página.", type=int, required=True)
    parser.add_argument("--termofinal", "-TF", help="Último termo terminado na página.", type=int, required=True)
    parser.add_argument("--ALF", "-ALF", help="Após confirmação, enviará a transcrição para o Alfresco.", nargs='?', type=str)
    args = parser.parse_args()

    console.log(os.environ.get('webdav_hostname'))

if __name__ == '__main__':
    console.log(f'[bold][red]Iniciando a composição do arquivo.')
    with console.status("[bold green] Processando...") as status:
        main()
    console.log(f'[bold][red]Processamento concluído!')
