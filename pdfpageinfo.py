#!/usr/bin/python
'''
    Como gerar o executável:
    pyinstaller --onefile pdfpageinfo.py 
'''
import os
import sys
import argparse
import fitz 
from rich.console import Console


def get_valid_format(value):
    valid_format = []
    for i in range(0, 11):
        valid_format.append("a{}".format(i))
        valid_format.append("b{}".format(i))
        valid_format.append("c{}".format(i))
    valid_format.append("card-4x6")
    valid_format.append("card-5x7")
    valid_format.append("commercial")
    valid_format.append("executive")
    valid_format.append("invoice")
    valid_format.append("ledger")
    valid_format.append("legal")
    valid_format.append("legal-13")
    valid_format.append("letter")
    valid_format.append("monarch")
    valid_format.append("tabloid-extra")

    if value is None:
        if console:
            console.log("[green]Definindo a dimensão da folha:[/green] a2")
        else:    
            print("Definindo a dimensão da folha: a2")
        return "a2"

    if value.lower() in valid_format:
        if console:
            console.log("[green]Definindo a dimensão da folha:[/green] {}".format(value.lower()))
        else:
            print("Formato de destino: {}".format(value.lower()))
        return value
    else:
        if console:
            console.log("[red]Formato não reconhecido.[/red] Será utilizado o formato de destino padrão: a2")
        else:
            print("Formato não reconhecido. Será utilizado o formato de destino padrão: a2")
        return "a2"

def pixel2cm(value):
    return (value / 72) * 2.54

def info(filesname, console = None):
    for filename in filesname:
        try:
            if console:
                console.log("[green]Obtendo metadados do arquivo:[/green] {}".format(filename))
            doc = fitz.open(filename)
            for i in range(doc.pageCount):
                page = doc.load_page(i)
                if console:
                    console.log("[green]Página {}:[/green] {} cm x {} cm.".format(i, pixel2cm(page.rect.height), pixel2cm(page.rect.width)))
            #print(dir(doc))
        except:
            if console:
                console.log("[green]Erro ao tentar abrir o arquivo:[/green] {}".format(filename))

def resize2A2(filesname, size_type, tmpdir = "", console = None):
    for filename in filesname:
        src = fitz.open(filename)
        doc = fitz.open()
        for ipage in src:
            if ipage.rect.width > ipage.rect.height:
                fmt = fitz.paper_rect(size_type + "-l")  # landscape if input suggests
            else:
                fmt = fitz.paper_rect(size_type)
            page = doc.new_page(width = fmt.width, height = fmt.height)
            page.show_pdf_page(page.rect, src, ipage.number)

        new_filename = "{}_{}".format(size_type, filename)
        if len(tmpdir) > 0:
            new_filename = os.path.join(tmpdir, new_filename)

        doc.save(new_filename)
        info([new_filename], console = console)

def get_filesname(pdfargs):
    filesname = []
    if isinstance(pdfargs, list):
        for f in pdfargs:
            if isinstance(f, list):
                for n in f:
                    filesname.append(n)
            else:
                filesname.append(f)
    elif isinstance(pdfargs, str):
        filesname.append(pdfargs)
    return list(filesname)
    
def main():
    help_dim = """
        Redimensiona as páginas do arquivo. O tamanho padrão é o A2, mas é possível especificar outros formatos. Dimensões reconhecidas pelo sistema:
        - de a0 até a10; 
        - de b0 até b10;
        - de c0 até c10;
        - card-4x6;
        - card-5x7;
        - commercial;
        - executive;
        - invoice;
        - ledger;
        - legal;
        - legal-13;
        - letter;
        - monarch;
        - tabloid-extra.
    """

    parser = argparse.ArgumentParser()
    parser.add_argument("input", nargs="?", help="Nome do arquivo PDF.")
    parser.add_argument("--pdfs", "-f", help="Nomes dos arquivos PDF.", action='append', nargs='+', type=str)
    parser.add_argument("--resize", "-r", nargs='?', default=False, help=help_dim)

    is_resize = False

    args = parser.parse_args()
    filesname = []

    if args.resize is not False:
        default_size = get_valid_format(args.resize)
        is_resize = True

    if args.input is not None:
        for item in get_filesname(args.input):
            filesname.append(item)

    if args.pdfs is not None:
        for item in get_filesname(args.pdfs):
            filesname.append(item)

    if len(filesname) > 0:
        info(filesname)
        if is_resize:
            resize2A2(filesname, default_size)

if __name__ == '__main__':
    main()