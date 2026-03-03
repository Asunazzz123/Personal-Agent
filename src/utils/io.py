import json
import os
from typing import Any, Dict, Iterable, List
import pandas as pd
from docx import Document

def ensure_dir(path: str)-> None:
    os.makedirs(path, exist_ok=True)

def read_audio(path: str) -> bytes:
    with open(path, "rb") as f:
        return f.read()

def read_csv(path: str) -> pd.DataFrame:
    return pd.read_csv(path) 

def read_markdown(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def write_word(path:str, content:str)-> None:
    
    doc = Document()
    doc.add_paragraph(content)
    doc.save(path)

def write_jsonl(path: str, rows: Iterable[Dict[str, Any]]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=True))
            f.write("\n")

def write_excel(path: str, data: List[Dict[str, Any]]) -> None:
    df = pd.DataFrame(data)
    df.to_excel(path, index=False)
