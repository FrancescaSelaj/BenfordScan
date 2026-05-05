# orchestratore.py
import ollama
from rag_interno import query_rag
from agente_web import query_agente_web

LLM_MODEL = "llama3.2"


def classifica_query(domanda: str) -> str:
    domanda_lower = domanda.lower()

    parole_interne = [
        "anomalia", "anomalie", "benford", "soglia", "dataset",
        "frode rilevata", "risultati", "prefisso", "seconda cifra",
        "prima cifra", "scarto", "analisi", "transazioni",
        "legittime", "fraudolente", "tasso di frode", "importi",
        "card testing", "soglie"
    ]

    parole_esterne = [
        "trend", "attuali", "normativa", "notizie", "europa",
        "mercato globale", "psd2", "banca centrale", "regolamento",
        "settore", "industry", "frodi emergenti", "pagamenti digitali"
    ]

    parole_ibride = [
        "coerenti con", "corrispondono ai", "in linea con",
        "confronto con", "rispetto ai trend", "confermati dal mercato",
        "pattern di frode noti", "nel settore", "sono compatibili", "sono coerenti", 
        "rispetto al mercato"
    ]

    ha_interno = any(p in domanda_lower for p in parole_interne)
    ha_esterno = any(p in domanda_lower for p in parole_esterne)
    ha_ibrido = any(p in domanda_lower for p in parole_ibride)

    if ha_ibrido:
        return "ibrida"

    if ha_esterno and not any(p in domanda_lower for p in [
        "nostre anomalie",
        "anomalie trovate",
        "nostri risultati",
        "risultati interni",
        "dataset",
        "analisi di benford"
    ]):
        return "esterna"

    if ha_interno and ha_esterno:
        return "ibrida"

    if ha_interno:
        return "interna"

    if ha_esterno:
        return "esterna"

    system_prompt = """Classifica la query:
- interna: dati interni aziendali, analisi, risultati, dataset, Benford
- esterna: trend, notizie, normative pubbliche, mercato
- ibrida: confronto tra risultati interni e contesto esterno

Rispondi SOLO con una parola: interna, esterna, ibrida.
"""

    response = ollama.chat(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": domanda},
        ],
        options={"temperature": 0}
    )

    risposta = response["message"]["content"].strip().lower()

    for categoria in ["ibrida", "interna", "esterna"]:
        if categoria in risposta:
            return categoria

    return "interna"


def anonimizza_query(domanda: str) -> str:
    system_prompt = """Riscrivi la domanda come query di ricerca web.

Regole:
- NON rispondere alla domanda
- NON spiegare
- NON inventare esempi, aziende, numeri o scenari
- Scrivi SOLO parole chiave
- Max 10 parole
- Mantieni solo il tema generale utile alla ricerca pubblica

Esempio:
Input: "Le anomalie trovate sono coerenti con i pattern di frode noti nel settore?"
Output: "card testing fraud patterns europe payment fraud"

Input: "I nostri risultati Benford sono coerenti con le frodi attuali?"
Output: "Benford law card testing fraud Europe"

Restituisci SOLO la query.
"""

    response = ollama.chat(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": domanda},
        ],
        options={"temperature": 0}
    )

    query_sicura = response["message"]["content"].strip()

    print(f"[Anonimizzazione] Query originale: '{domanda}'")
    print(f"[Anonimizzazione] Query esterna sicura: '{query_sicura}'")

    return query_sicura


def orchestra(domanda: str, file_dati: str = "data/risultati_benford.txt") -> dict:
    print(f"\n[Orchestratore] Analisi query: '{domanda}'")

    tipo = classifica_query(domanda)
    print(f"[Orchestratore] Classificata come: {tipo.upper()}")

    if tipo == "interna":
        print("[Orchestratore] → RAG interno (dati privati, no web)")

        risposta = query_rag(domanda, file_dati)

        return {
            "tipo": "interna",
            "risposta": risposta,
            "fonti": "Dati interni riservati (elaborazione locale)"
        }

    elif tipo == "esterna":
        print("[Orchestratore] → Agente web (fonti pubbliche)")

        risposta = query_agente_web(domanda)

        return {
            "tipo": "esterna",
            "risposta": risposta,
            "fonti": "Fonti pubbliche web"
        }

    else:
        print("[Orchestratore] → Query ibrida: RAG interno + Agente web")
        print("[Orchestratore] Applicazione anonimizzazione prima della ricerca web...")

        risposta_interna = query_rag(domanda, file_dati)
        query_esterna = anonimizza_query(domanda)
        risposta_esterna = query_agente_web(query_esterna)

        system_prompt_sintesi = """Sei un analista aziendale senior.

Hai accesso a due fonti distinte:
1. Dati interni aziendali riservati
2. Contesto di mercato esterno da fonti pubbliche

Sintetizza entrambe le fonti in una risposta chiara per il decisore.

Regole:
- Prima riassumi i risultati interni Benford.
- Poi confrontali con il contesto esterno.
- Spiega chiaramente se i pattern interni sono coerenti o no con le frodi note.
- Distingui cosa deriva dai dati interni e cosa deriva dal contesto esterno.
- Non inventare dati.
- Sii conciso, operativo e orientato alla decisione.
"""

        response = ollama.chat(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": system_prompt_sintesi},
                {
                    "role": "user",
                    "content": f"""Domanda originale dell'analista:
{domanda}

DATI INTERNI AZIENDALI:
{risposta_interna}

CONTESTO DI MERCATO ESTERNO:
{risposta_esterna}

Fornisci una sintesi integrata per supportare la decisione."""
                }
            ],
            options={"temperature": 0}
        )

        return {
            "tipo": "ibrida",
            "risposta": response["message"]["content"],
            "fonti": "Dati interni (privati) + Mercato esterno (anonimizzato)"
        }