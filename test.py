from dotenv import load_dotenv
from pdftranscricao import find_av_from_current_dir

from rich.console import Console

console = Console()
load_dotenv()
console.log("Start.")

termo_inicial = 2250
termo_final = 2255
registros = list(range(int(termo_inicial),int(termo_final+1),1))

a, b, c = find_av_from_current_dir(registros, console = console)

console.log(a, b, c)