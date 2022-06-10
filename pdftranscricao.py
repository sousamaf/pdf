import os
import glob
import shutil
import argparse
import tempfile
import subprocess
from sys import platform
from dotenv import load_dotenv
from pdftools import pdf_merge
from pdfcompress import compress
from pdfpageinfo import resize2A2
from webdav3.client import Client
from PyPDF2 import PdfFileReader, PdfFileMerger

from rich.panel import Panel
from rich.console import Console
from rich.progress import Progress
from rich.prompt import Confirm

'''
    Como gerar o executável:
    pyinstaller --onefile pdftranscricao.py
'''

home = os.environ.get("HOME")
load_dotenv(dotenv_path=os.path.join(home, ".env"))

def show_message(message = "", console = None):
    if os.environ.get('VERBOSE') == 'enable':
        if console:
            console.log(message)
        else:
            print(message)


def find_av_from_current_dir(registros, console = None):
    console.log("[green]Buscando av.[/green]")
    files = []
    files_card = []
    files_min_card = []

    local_dir = os.getcwd()
    for i, v in enumerate(registros):
        full_path = os.path.join(local_dir, "av{}.pdf".format(v))
        if len(glob.glob(full_path)) > 0:
            full_path_card = "card-5x7_av{}.pdf".format(v)
            full_path_min_card = "min_card-5x7_av{}.pdf".format(v)

            files.append(os.path.basename(full_path))
            files_card.append(full_path_card)
            files_min_card.append(full_path_min_card)
            console.log("[green]Av encontrada:[/green] {}".format(full_path))

    return [files, files_card, files_min_card]

def submit_to_alfresco(alfresco_dir_name, file_name, console = None):
    options = {
        'webdav_hostname': os.environ.get('PDF_WEBDAV_HOSTNAME'),
        'webdav_login': os.environ.get('PDF_WEBDAV_LOGIN'),
        'webdav_password': os.environ.get('PDF_WEBDAV_PASSWORD')
    }
    client = Client(options)
    paraSalvarAlfresco = "{}{}".format(alfresco_dir_name, file_name)
    paraSalvarPDF = os.path.join(os.getcwd(), file_name)
    if console:
        console.log("[green]{}[/green]".format(paraSalvarAlfresco))
    #print(paraSalvarAlfresco)
    client.upload_sync(remote_path=paraSalvarAlfresco, local_path=paraSalvarPDF)

def copy_to_nas(livro, file_name):
    path_on_nas_folder = os.environ.get('PATH_ON_NAS_FOLDER').format(livro)
    #print(path_on_nas_folder)

    shutil.copy2(file_name, path_on_nas_folder)



def pdf_details_update( file_input,
                        author = "",
                        title = "",
                        subtitle = "",
                        console = None
                    ):
    file_in = open(file_input, 'rb')
    pdf_reader = PdfFileReader(file_in)
    metadata = pdf_reader.getDocumentInfo()

    pdf_meta_merger = PdfFileMerger()
    pdf_meta_merger.append(file_in)
    pdf_meta_merger.addMetadata({
        '/Author': author,
        '/Title': title,
        '/Subtitle' : subtitle,
        '/Description' : title + subtitle,
        '/Subject': title + subtitle,
    })
    file_out = open("new_{}".format(file_input), 'wb')
    pdf_meta_merger.write(file_out)

    file_in.close()
    file_out.close()

def merge_pages(livro, pagina, termo_inicial, termo_final, dupla = False, console = None):
    arq_t = 2
    arq = 1

    if console:
        console.log(f"[green]Coletando número de termos[/green]")
    output_files = ["{}{}.pdf".format(pagina,'a'), "{}{}.pdf".format(pagina,'b')]
    if dupla:
        pagina2 = int(pagina) + 1
        output_files.append("{}{}.pdf".format(pagina2,'a'))
        output_files.append("{}{}.pdf".format(pagina2,'b'))

    output_files_a2 = ["a2_{}".format(file_name) for file_name in output_files]
    output_files_min_a2 = ["min_a2_{}".format(file_name) for file_name in output_files]

    output_files_text_min_a2 = " ".join(str(s) for s in output_files_min_a2)

    registros = list(range(int(termo_inicial),int(termo_final+1),1))
    output_registros = ["Termo {}".format(reg) for reg in registros ]
    output_registros_text = " ".join(str(s) for s in output_registros)

    local_dir = os.getcwd()

    ## av
    avs, avs_card, avs_min_card = find_av_from_current_dir(registros, console = console)

    # make a temporary dir and process all the files.
    with tempfile.TemporaryDirectory() as tmpdirname:
        if console:
            console.log(f"[green]Criação de espaço de trabalho temporário[/green]: {tmpdirname}")
            console.log(f"[green]Redimensionando páginas[/green]")
        # print('created temporary directory', tmpdirname)
        # print('Resize all page to A2:')
        resize2A2(output_files, 'a2', tmpdirname, console = console)

        # avs
        if len(avs) > 0:
            resize2A2(avs, 'card-5x7', tmpdirname, console = console)

        os.chdir(tmpdirname)
        if console:
            console.log(f"[green]Compactando arquivos[/green]")
        for i, v in enumerate(output_files_a2):
            compress(v, output_files_min_a2[i], power=3, console = console)

        for i, v in enumerate(avs_card):
            compress(v, avs_min_card[i], power=3, console = console)
            output_files_min_a2.append(avs_min_card[i])

        pdf_merge(output_files_min_a2, 'livro_pagina.pdf')

        final_file_name = "Livro {} p{} {}.pdf".format(livro, pagina,
        output_registros_text)

        if console:
            console.log(f"[green]Atualizando metadados do arquivo final.[/green]")
        pdf_details_update("livro_pagina.pdf",
                            author = "Marco Antonio",
                            title = final_file_name.replace(".pdf", " "),
                            subtitle = output_registros_text,
                            console = console)

        final_path_file_name = os.path.join(local_dir, final_file_name)
        if console:
            console.log(f"[green]Finalizando arquivo e copiando do espaço temporário[/green]")
        shutil.copy2('new_livro_pagina.pdf', final_path_file_name)
        os.chdir(local_dir)
        return final_file_name

def main(console):
    parser = argparse.ArgumentParser()
    parser.add_argument("--livro", "-L", help="Código do livro. Por exemplo: 3-G.", type=str, required=True)
    parser.add_argument("--pagina", "-P", help="Página do livro.", type=str, required=True)
    parser.add_argument("--termoinicial", "-TI", help="Primeiro Termo completo na página.", type=int, required=True)
    parser.add_argument("--termofinal", "-TF", help="Último termo terminado na página.", type=int, required=True)
    parser.add_argument("--dupla", help="Folha dupla", action = 'store_true')
    parser.add_argument("--PUB", "-PUB", help="Após confirmação, enviará o documento final para NAS e Alfresco.", nargs='?', type=str)
    args = parser.parse_args()

    livro = args.livro
    pagina = args.pagina
    termo_inicial = args.termoinicial
    termo_final = args.termofinal
    dupla = False
    if args.dupla:
        dupla = True

    console.log(f'[bold][red]Iniciando a composição do arquivo.')
    final_file_name = merge_pages(livro, pagina, termo_inicial, termo_final, dupla = dupla, console = console)
    if args.PUB:
        status.update("[red]Publicar arquivo no NAS e Alfresco?[/red]")
        if Confirm.ask(""):
            console.log("[green]Publicando.[/]")
            path_on_alfresco = os.environ.get('PDF_PATH_ON_ALFRESCO')

            dirAlfresco = str(path_on_alfresco.format(livro))
            submit_to_alfresco(dirAlfresco, final_file_name, console = console)
            copy_to_nas(livro, final_file_name)
        else:
            console.log("[red]Gerou apenas arquivo local.[/red]")

if __name__ == '__main__':
    console = Console()
    with console.status("[bold green] Processando...") as status:
        main(console)
    console.log(f'[bold][red]Processamento concluído!')
