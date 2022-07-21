import os
import re
import click
import shutil
import tempfile
from sys import platform
from PyPDF2 import PdfMerger
from PyPDF2 import PdfReader
from PyPDF2 import PdfWriter
from dotenv import load_dotenv
from rich.console import Console
from pdfpageinfo import resize2A2
from webdav3.client import Client
from rich.progress import Progress
from PyPDF2 import PdfFileReader, PdfFileMerger

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


def pdf_merger(filesname, output, tmpdir = ""):
    merger = PdfMerger()

    if len(tmpdir) > 0:
        output = os.path.join(tmpdir, output)


    for pdf in filesname:
        if check_if_exists(pdf):
            merger.append(pdf)
        else:
            console.log("[red]O arquivo {} não existe.[/red]".format(pdf))
    if len(merger.pages):
        merger.write(output)
    else:
        console.log("\n[red]***Nenhum arquivo de saída foi criado.***[/red]\n".format(pdf))
    merger.close()


def pdf_compresser(filename, output, tmpdir = ""):

    if check_if_exists(filename):
        reader = PdfReader(filename)
        writer = PdfWriter()

        for page in reader.pages:
            page.compress_content_streams()
            writer.add_page(page)
        
        if len(tmpdir) > 0:
            output = os.path.join(tmpdir, output)

        with open(output, "wb") as f:
            writer.write(f)
    else:
        console.log("[red]O arquivo {} não existe.[/red]".format(filename))


def pdf_resizer(filename, s, tmpdir = "", console = None):
    resize2A2(filename, size_type = s, tmpdir = tmpdir, console = console)

def pdf_details_updater( file_input,
                        author = "",
                        title = "",
                        subtitle = "",
                        o = "",
                        tmpdir = "",
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
    if len(o) > 0:
        new_file = o
    else:
        new_file = "new_{}".format(file_input)

    file_out = open(new_file, 'wb')
    pdf_meta_merger.write(file_out)

    file_in.close()
    file_out.close()

def copy_to_nas(livro, file_name):
    path_on_nas_folder = os.environ.get('PATH_ON_NAS_FOLDER').format(livro)
    shutil.copy2(file_name, path_on_nas_folder)

def submiter_to_alfresco(alfresco_dir_name, file_name, console = None):
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
    # print(paraSalvarAlfresco)
    client.upload_sync(remote_path=paraSalvarAlfresco, local_path=paraSalvarPDF)

def processor(livro, pagina, termoinicial, termofinal, author, title, subtitle, dupla):
    with Progress() as progress:
        task1 = progress.add_task("[green]Processando...", total=100)
        while not progress.finished:
            # click.secho("Preparando entrada")
            progress.update(task1, advance=3)

            pdf_input = ["{}a.pdf".format(pagina), "{}b.pdf".format(pagina)]
            if dupla:
                pagina2 = int(pagina) + 1
                pdf_input.append("{}a.pdf".format(pagina2))
                pdf_input.append("{}b.pdf".format(pagina2))

            pdf_files_a2 = ["a2_{}".format(file_name) for file_name in pdf_input]

            registros = list(range(int(termoinicial),int(termofinal)+1,1))
            output_registros = ["Termo {}".format(reg) for reg in registros ]
            output_registros_text = " ".join(str(s) for s in output_registros)

            final_file_name = "Livro {} p{} {}.pdf".format(livro, pagina,
                output_registros_text)

            # click.secho("Capturando local")
            progress.update(task1, advance=2)

            local_dir = os.getcwd()
            with tempfile.TemporaryDirectory() as tmpdirname:
                
                # click.secho("Redimensionando as páginas dos arquivos de entrada")
                progress.update(task1, advance=15)

                pdf_resizer(pdf_input, 'a2', tmpdir=tmpdirname)
                os.chdir(tmpdirname)

                # click.secho("Componto arquivo")
                progress.update(task1, advance=7)

                pdf_merger(pdf_files_a2, output='merged.pdf', tmpdir=tmpdirname)

                # click.secho("Compactando o arquivo PDF")
                progress.update(task1, advance=20)

                pdf_compresser('merged.pdf', 'compressed.pdf', tmpdir=tmpdirname)

                # click.secho("Atualizando metadados")
                progress.update(task1, advance=13)

                pdf_details_updater("compressed.pdf",
                                    author = author,
                                    title = final_file_name.replace(".pdf", " "),
                                    subtitle = output_registros_text,
                                    o = "final.pdf",
                                    console = console)
                
                # click.secho("Gerando arquivo final")
                progress.update(task1, advance=25)

                final_path_file_name = os.path.join(local_dir, final_file_name)
                shutil.copy2('final.pdf', final_path_file_name)
                os.chdir(local_dir)

                # click.secho("Processo concluído")
                progress.update(task1, advance=15)

def publisher(filesname, re, livro):
    if len(filesname) > 0:
        for f in filesname:
            if check_if_exists(f):
                print("Publicando o arquivo {} no livro {}".format(f, livro))
                # to_nas(filename, livro)
                # to_alfresco(filename, livro)

    # res = [f for f in os.listdir(path) if re.search(r'(abc|123|a1b).*\.txt$', f)]
# for f in res:
#     print f

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


@pdf.command()
@click.argument('filename', type=str, nargs=-1)
@click.option("-s", type=str, default="a2")
def resizer(filename, s):
    """Realiza o dimensionamento de cada página do arquivo PDF."""
    pdf_resizer(filename, s)


@pdf.command()
@click.argument('filename')
@click.option("--author", "-a", "author", default="")
@click.option("--title", type=str, default="")
@click.option("--subtitle", type=str, default="")
@click.option('-o', default="")
def details_update(filename, author, title, subtitle, o):
    """Realiza a atualização de metadados do arquivo PDF."""
    pdf_details_updater(filename, author, title, subtitle, o)

@pdf.command()
@click.argument('filename')
@click.option("--livro", "-l", required=True, help="Número do livro.")
def to_nas(filename, livro):
    """Realiza a cópia do arquivo PDF para o NAS."""
    copy_to_nas(livro, filename)

@pdf.command()
@click.argument('filename')
@click.option("--livro", "-l", required=True, help="Número do livro.")
def to_alfresco(filename, livro):
    """Publica o arquivo PDF no Alfresco."""
    path_on_alfresco = os.environ.get('PDF_PATH_ON_ALFRESCO')
    alfresco_dir_name = str(path_on_alfresco.format(livro))

    submiter_to_alfresco(alfresco_dir_name, filename)

@pdf.command()
@click.option("--livro", "-l", required=True, help="Número do livro.")
@click.option("--pagina", "-p", type=str, required=True)
@click.option("--termoinicial", "-ti", required=True)
@click.option("--termofinal", "-tf", required=True)
@click.option("--author", "-a", "author", default="")
@click.option("--title", type=str, default="")
@click.option("--subtitle", type=str, default="")
@click.option("--dupla", "-d", is_flag=True, default=False)
def process(livro, pagina, termoinicial, termofinal, author, title, subtitle, dupla):
    """Realiza o processamento completo dos arquivos de entrada."""
    processor(livro, pagina, termoinicial, termofinal, author, title, subtitle, dupla)

@pdf.command()
@click.argument('filename', type=str, nargs=-1)
@click.option("--re", type=str, required=False, help="Expressão Regular para buscar arquivos.")
@click.option("--livro", "-l", required=True, help="Número do livro.")
def publish(filename, re, livro):
    """Realiza a publicação de arquivo ou lista de arquivos no NAS e Alfresco."""
    publisher(filename, re, livro)

if __name__ == '__main__':
    console = Console()
    pdf()