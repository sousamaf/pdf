#!/usr/bin/python
'''
    Como gerar o executável:
    pyinstaller --onefile pdfmetaupdate.py 
'''
import os
import sys
import argparse
from PyPDF2 import PdfReader, PdfMerger

def meta_update(file_input, author = "", title = "", description = ""):
    file_in = open(file_input, 'rb')
    pdf_reader = PdfReader(file_in)
    metadata = pdf_reader.metadata

    pdf_meta_merger = PdfMerger()
    pdf_meta_merger.append(file_in)

    pdf_meta_merger.add_metadata(metadata)

    if bool(author.strip()):
        pdf_meta_merger.add_metadata({
            '/Author': author,
        })

    if bool(title.strip()):
        pdf_meta_merger.add_metadata({
            '/Title': title,
        })

    if bool(description.strip()):
        pdf_meta_merger.add_metadata({
            '/Subject' : description,
        })


    file_out = open(file_input, 'wb')
    pdf_meta_merger.write(file_out)

    file_in.close()
    file_out.close()

def main():
    help_dim = """
        Atualização de metadados de arquivos PDF. Atributos possíveis:
        - title: Título do documento;
        - author: Nome do autor do documento;
        - description: Detalhes do documento.
    """

    parser = argparse.ArgumentParser(prog = 'pdfmetaupdate', description = 'Update metadados de arquivo PDF'	)
    parser.add_argument("input", help="Nome do arquivo PDF.")
    
    parser.add_argument("--title", "-t", help="Atribuição do Título do documento.", type=str, required=False)
    parser.add_argument("--author", "-a", help="Atribuição do Autor do documento.", type=str)
    parser.add_argument("--description", "-d", help="Atribuição da Descrição do documento.", type=str)

    args = parser.parse_args()
    title, author, description = " ", " ", " "

    if args.title is not None:
        title = args.title
    if args.author is not None:
        author = args.author
    if args.description is not None:
        description = args.description
        
    if bool(title.strip()) or bool(author.strip()) or bool(description.strip()):
        meta_update(file_input = args.input, author = author, title = title, description = description)
    else:
        print("Nenhuma ação realizada. Informe pelo menos um atributo para atualização.")


if __name__ == '__main__':
    main()
