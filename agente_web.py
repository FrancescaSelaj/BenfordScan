# agente_web.py
import ollama

LLM_MODEL = "llama3.2"


def migliora_query_web(domanda: str) -> str:
    """
    Trasforma la domanda in una query web più precisa.
    Serve per evitare risultati generici o poco pertinenti.
    """

    domanda_lower = domanda.lower()

    if "card fraud" in domanda_lower or "card testing" in domanda_lower:
        return "Europe card testing fraud card-not-present fraud PSD2 SCA payment fraud trends 2024 2025"

    if "psd2" in domanda_lower or "sca" in domanda_lower or "normativa" in domanda_lower:
        return "Europe PSD2 SCA payment fraud regulation card fraud"

    if "frodi" in domanda_lower or "frode" in domanda_lower:
        return "Europe payment fraud trends card fraud ecommerce fraud"

    return domanda


def web_search_tool(query: str) -> str:
    """
    Esegue una ricerca web su fonti esterne.
    Richiede: pip install ddgs
    """

    try:
        from ddgs import DDGS

        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=5))

            if not results:
                return "Nessun risultato web trovato."

            testi = []
            for r in results:
                titolo = r.get("title", "Titolo non disponibile")
                url = r.get("href", "URL non disponibile")
                corpo = r.get("body", "")

                testi.append(
                    f"TITOLO: {titolo}\n"
                    f"FONTE: {url}\n"
                    f"CONTENUTO: {corpo}"
                )

            return "\n\n---\n\n".join(testi)

    except ImportError:
        return (
            "Ricerca web non disponibile: il pacchetto ddgs non è installato. "
            "Installa con: pip install ddgs"
        )

    except Exception as e:
        return f"Errore durante la ricerca web: {str(e)}"


def query_agente_web(domanda: str) -> str:
    """
    Usa solo fonti esterne pubbliche.
    Non ha accesso ai dati aziendali interni.
    """

    query_web = migliora_query_web(domanda)
    risultati_web = web_search_tool(query_web)

    SYSTEM_PROMPT = """Sei un analista di mercato specializzato in fraud detection e pagamenti digitali.

Regole obbligatorie:
- Usa SOLO le informazioni presenti nei risultati web forniti.
- NON usare dati aziendali interni.
- NON inventare statistiche, fonti o trend.
- Se i risultati web sono deboli o non pertinenti, dichiaralo esplicitamente.
- Ignora fonti non pertinenti rispetto a card fraud, payment fraud, card testing, PSD2, SCA o frodi digitali.
- Rispondi in italiano.
- Mantieni un tono professionale e sintetico.

Quando possibile, organizza la risposta in:
1. Trend principali
2. Implicazioni per le aziende
3. Collegamento con fraud detection
"""

    response = ollama.chat(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"""Domanda originale:
{domanda}

Query web usata:
{query_web}

Risultati dalla ricerca web:
{risultati_web}

Produci una sintesi professionale per un analista aziendale."""
            },
        ],
        options={"temperature": 0}
    )

    return response["message"]["content"]