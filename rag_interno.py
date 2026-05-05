#rag_interno.py
import ollama
import os
import json
import numpy as np
from numpy.linalg import norm

EMBEDDING_MODEL = "bge-m3"
LLM_MODEL = "llama3.2"
EMBEDDINGS_DIR = "embeddings"

def parse_file(filename):
    with open(filename, encoding="utf-8-sig") as f:
        paragraphs = []
        buffer = []
        for line in f.readlines():
            line = line.strip()
            if line:
                buffer.append(line)
            elif len(buffer):
                paragraphs.append(" ".join(buffer))
                buffer = []
        if len(buffer):
            paragraphs.append(" ".join(buffer))
    return paragraphs

def save_embeddings(nome_chiave, embeddings):
    os.makedirs(EMBEDDINGS_DIR, exist_ok=True)
    with open(f"{EMBEDDINGS_DIR}/{nome_chiave}.json", "w") as f:
        json.dump(embeddings, f)

def load_embeddings(nome_chiave):
    path = f"{EMBEDDINGS_DIR}/{nome_chiave}.json"
    if not os.path.exists(path):
        return False
    with open(path, "r") as f:
        return json.load(f)

def get_embeddings(filename, chunks):
    nome_chiave = os.path.basename(filename).replace(".txt", "")
    if (embeddings := load_embeddings(nome_chiave)) is not False:
        return embeddings
    embeddings = [
        ollama.embeddings(model=EMBEDDING_MODEL, prompt=chunk)["embedding"]
        for chunk in chunks
    ]
    save_embeddings(nome_chiave, embeddings)
    return embeddings

def find_most_similar(needle, haystack):
    needle_norm = norm(needle)
    scores = [
        np.dot(needle, item) / (needle_norm * norm(item))
        for item in haystack
    ]
    return sorted(zip(scores, range(len(haystack))), reverse=True)

def query_rag(domanda: str, filename: str = "data/risultati_benford.txt") -> str:
    SYSTEM_PROMPT = """Sei un analista che risponde SOLO usando il contesto fornito.

Regole obbligatorie:
- Usa solo informazioni presenti nel contesto.
- Non inventare.
- Non fare calcoli.
- Se il dato non è presente, rispondi: "Non presente nel contesto".
- Se la domanda parla di "prefisso" o "prime due cifre", devi usare SOLO la sezione "RISULTATI PRIME DUE CIFRE".
- Se la domanda parla di "seconda cifra", devi usare SOLO la sezione "RISULTATI SECONDA CIFRA".
- Se la domanda parla di "soglia critica", interpreta "critica" come "soglia con segnale ATTENZIONE".
- Rispondi in modo breve e diretto.

Contesto:
"""

    chunks = parse_file(filename)
    embeddings = get_embeddings(filename, chunks)

    prompt_embedding = ollama.embeddings(
        model=EMBEDDING_MODEL,
        prompt=domanda
    )["embedding"]

    top_chunks = find_most_similar(prompt_embedding, embeddings)[:10]
    top_chunks = sorted(top_chunks, key=lambda x: x[1])

    # ---- chunk recuperati (decommentare se necessario) ----
    # print("\n--- CHUNK USATI ---")
    # for item in top_chunks:
    #     print(chunks[item[1]])

    response = ollama.chat(
        model=LLM_MODEL,
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT + "\n".join(
                    chunks[item[1]] for item in top_chunks
                ),
            },
            {"role": "user", "content": domanda},
        ],
        options={"temperature": 0}
    )

    return response["message"]["content"]