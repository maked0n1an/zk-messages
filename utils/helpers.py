import json
from pathlib import Path


def read_txt(filepath: Path | str):
    with open(filepath, 'r') as file:
        return [row.strip() for row in file]
    
def read_json(filepath: Path | str):
    with open(filepath, 'r') as file:
        return json.load(file)
    
def format_output(message: str):
    print(f"{message:^80}")