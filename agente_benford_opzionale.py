# agente_benford_opzionale.py
import ollama
import pandas as pd

LLM_MODEL = "llama3.2"


def interpreta_risultati():
    """
    Agente interpretativo opzionale.

    Pattern agentico:
    risultati Benford già calcolati → LLM Agent → report testuale.

    Questo file NON è necessario per far funzionare main.py.
    Serve solo per generare un report discorsivo aggiuntivo.
    """

    descrittiva = pd.read_excel(
        "analisi_benford_output.xlsx",
        sheet_name="1_Descrittiva"
    )

    prima_cifra = pd.read_excel(
        "analisi_benford_output.xlsx",
        sheet_name="2_Prima_cifra"
    )

    seconda_cifra = pd.read_excel(
        "analisi_benford_output.xlsx",
        sheet_name="3_Seconda_cifra"
    )

    prime_due_cifre = pd.read_excel(
        "analisi_benford_output.xlsx",
        sheet_name="4_Prime_due_cifre"
    )

    soglie = pd.read_excel(
        "analisi_benford_output.xlsx",
        sheet_name="5_Soglie_aziendali"
    )

    sintesi = pd.read_excel(
        "analisi_benford_output.xlsx",
        sheet_name="6_Sintesi_anomalie"
    )

    contesto_risultati = f"""
ANALISI BENFORD'S LAW - FRAUD DETECTION

DESCRITTIVA:
{descrittiva.to_string(index=False)}

RISULTATI PRIMA CIFRA:
{prima_cifra.round(3).to_string(index=False)}

RISULTATI SECONDA CIFRA:
{seconda_cifra.round(3).to_string(index=False)}

RISULTATI PRIME DUE CIFRE:
{prime_due_cifre.round(3).to_string(index=False)}

ANALISI SOGLIE AZIENDALI:
{soglie.to_string(index=False)}

SINTESI ANOMALIE:
{sintesi.to_string(index=False)}
"""

    SYSTEM_PROMPT = """Sei un analista forense specializzato in fraud detection.

Hai ricevuto i risultati di un'analisi di Benford's Law applicata a transazioni finanziarie.

Regole:
- Usa solo i risultati forniti.
- Non inventare numeri.
- Non dire che una deviazione prova automaticamente una frode.
- Interpreta le anomalie come segnali di rischio.
- Collega i risultati al possibile pattern di card testing fraud.
- Rispondi in italiano.
- Mantieni un tono professionale e orientato alla decisione.
"""

    print("\n[Agente Benford] Generazione report in corso...\n")
    print("=" * 60)

    response = ollama.chat(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"""Interpreta questi risultati e produci un report:

{contesto_risultati}

Struttura il report in:
1. Sintesi esecutiva
2. Anomalie principali
3. Interpretazione fraud detection
4. Soglie da monitorare
5. Caveat metodologico
6. Raccomandazioni operative
"""
            }
        ],
        options={"temperature": 0}
    )

    report = response["message"]["content"]

    print(report)

    with open("report_fraud_detection.txt", "w", encoding="utf-8") as f:
        f.write("REPORT FRAUD DETECTION - BENFORD'S LAW\n")
        f.write("=" * 60 + "\n\n")
        f.write(report)

    print("\n" + "=" * 60)
    print("[Agente Benford] Report salvato: report_fraud_detection.txt")


if __name__ == "__main__":
    interpreta_risultati()