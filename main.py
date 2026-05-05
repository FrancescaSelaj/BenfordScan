# main.py
from orchestratore import orchestra

FILE_DATI = "data/risultati_benford.txt"

def main():
    print("=== BenfordScan: RAG locale + Agente Web ===")
    print("Modello LLM: llama3.2 via Ollama")
    print("Knowledge base: data/risultati_benford.txt")
    print("Digita 'exit' per uscire\n")
    
    while True:
        domanda = input("Analista → ").strip()
        if domanda.lower() == "exit":
            break
        if not domanda:
            continue
            
        risultato = orchestra(domanda, FILE_DATI)
        
        print(f"\n[Tipo query: {risultato['tipo'].upper()}]")
        print(f"[Fonti: {risultato['fonti']}]")
        print(f"\nRisposta:\n{risultato['risposta']}\n")
        print("-" * 60)

if __name__ == "__main__":
    main()