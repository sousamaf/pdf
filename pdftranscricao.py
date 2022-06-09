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

load_dotenv()

def submit_to_alfresco(alfresco_dir_name, file_name, console = None):
    options = {
        'webdav_hostname': os.environ.get('webdav_hostname'), 
        'webdav_login': os.environ.get('webdav_login'), 
        'webdav_password': os.environ.get('webdav_password')
    }
    console.log(options)
    client = Client(options)
    paraSalvarAlfresco = "{}{}".format(alfresco_dir_name, file_name)
    if console:
        console.log("[green]{}[/green]".format(paraSalvarAlfresco))
    # print("        :", paraSalvarAlfresco)
    # client.upload_sync(remote_path=paraSalvarAlfresco, local_path=paraSalvarPDF)

def pdf_details_update( file_input, 
                        author = "", 
                        title = "",
                        subtitle = "",
                        console = None
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

def merge_pages(livro, pagina, termo_inicial, termo_final, console = None):
    arq_t = 2
    arq = 1

    letra = "a"

    # arquivos = list(range(int(arq),arq + int(arq_t),1))
    if console:
        console.log(f"[green]Coletando número de termos[/green]")
    output_files = ["{}{}.pdf".format(pagina,'a'), "{}{}.pdf".format(pagina,'b')]
    output_files_a2 = ["a2_{}".format(file_name) for file_name in output_files]
    output_files_min_a2 = ["min_a2_{}".format(file_name) for file_name in output_files]

    output_files_text_min_a2 = " ".join(str(s) for s in output_files_min_a2)

    registros = list(range(int(termo_inicial),int(termo_final+1),1))
    output_registros = ["Termo {}".format(reg) for reg in registros ]
    output_registros_text = " ".join(str(s) for s in output_registros)

    local_dir = os.getcwd()

    # make a temporary dir and process all the files.
    with tempfile.TemporaryDirectory() as tmpdirname:
        if console:
            console.log(f"[green]Criação de espaço de trabalho temporário[/green]: {tmpdirname}")
            console.log(f"[green]Redimensionando página[/green]")
        # print('created temporary directory', tmpdirname)
        # print('Resize all page to A2:')
        resize2A2(output_files, 'a2', tmpdirname, console = console)
        
        os.chdir(tmpdirname)
        if console:
            console.log(f"[green]Compactando arquivo[/green]")
        for i, v in enumerate(output_files_a2):
            compress(v, output_files_min_a2[i], power=3, console = console)
        
        pdf_merge(output_files_min_a2, 'livro_pagina.pdf')
        
        final_file_name = "Livro {} p{}.pdf".format(livro, pagina)
        if console:
            console.log(f"[green]Atualizando metadados do arquivo[/green]")
        pdf_details_update("livro_pagina.pdf", 
                            author = "Marco Antonio", 
                            title = final_file_name,
                            subtitle = output_registros_text,
                            console = console)
        
        final_path_file_name = os.path.join(local_dir, final_file_name)
        if console:
            console.log(f"[green]Finalizando arquivo e copiando do espaço temporário[/green]")
        shutil.copy2('new_livro_pagina.pdf', final_path_file_name)
        os.chdir(local_dir)

def main(console):
    parser = argparse.ArgumentParser()
    parser.add_argument("--livro", "-L", help="Código do livro. Por exemplo: 3-G.", type=str, required=True)
    parser.add_argument("--pagina", "-P", help="Página do livro.", type=str, required=True)
    parser.add_argument("--termoinicial", "-TI", help="Primeiro Termo completo na página.", type=int, required=True)
    parser.add_argument("--termofinal", "-TF", help="Último termo terminado na página.", type=int, required=True)
    parser.add_argument("--ALF", "-ALF", help="Após confirmação, enviará a transcrição para o Alfresco.", nargs='?', type=str)
    args = parser.parse_args()

    livro = args.livro
    pagina = args.pagina
    termo_inicial = args.termoinicial
    termo_final = args.termofinal

    merge_pages(livro, pagina, termo_inicial, termo_final, console = console)

    if args.ALF:
        dirAlfresco = str("Sites/swsdp/documentLibrary/Registro de Imóveis/Transcrições das Transmissões/Livro {}/".format(args.livro))
        file_name = "Livro {} p{}.pdf".format(livro, pagina)
        alfresco = True
        # print("Alfresco:", dirAlfresco)
        submit_to_alfresco(dirAlfresco, file_name, console = console)

if __name__ == '__main__':
    console = Console()
    console.log(f'[bold][red]Iniciando a composição do arquivo.')
    with console.status("[bold green] Processando...") as status:
        main(console)
    console.log(f'[bold][red]Processamento concluído!')
