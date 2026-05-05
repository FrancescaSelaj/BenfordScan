# Fraud Detection con Benford's Law, RAG e Agent Orchestration

## Obiettivo del progetto

Il progetto implementa un sistema locale di fraud detection basato su Benford's Law.

Il workflow è composto da tre parti:

1. Analisi statistica delle transazioni tramite Benford's Law.
2. Trasformazione dei risultati in una knowledge base testuale interrogabile tramite RAG.
3. Orchestrazione agentica per distinguere domande interne, esterne e ibride.

L'obiettivo è mostrare come un'analisi di fraud detection possa essere integrata con un sistema RAG locale e con un agente web separato.

---

## Capitoli del corso coperti

- Ch. 2: uso locale di LLM open-source tramite Ollama.
- Ch. 3: RAG, embedding, chunking, retrieval e cosine similarity.
- Ch. 4: agenti, orchestrazione e separazione tra dati interni ed esterni.
- Ch. 5: Fraud Detection e Benford's Law.

---

## Dataset

Il progetto usa il dataset Credit Card Fraud Detection disponibile su Kaggle:

https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud

Per eseguire il progetto da zero, il file `creditcard.csv` deve essere scaricato da Kaggle e inserito nella cartella principale del progetto.

Il file `creditcard.csv` non è incluso nel repository perché supera il limite di dimensione consentito da GitHub.

Nel codice viene usata la colonna `Amount`, perché contiene gli importi reali delle transazioni.

Le colonne `V1-V28` non vengono usate per Benford's Law perché sono componenti PCA anonimizzate e quindi non interpretabili direttamente.

La colonna `Class` viene usata per distinguere:

- `0`: transazione legittima
- `1`: transazione fraudolenta

---

## Modelli usati

- LLM: `llama3.2`
- Embedding model: `bge-m3`

Entrambi vengono eseguiti localmente tramite Ollama.

---

## Struttura del progetto

```text
BenfordScan/
│
├── data/
│   └── risultati_benford.txt
│
├── agente_benford_opzionale.py
├── agente_web.py
├── analisi_benford.py
├── main.py
├── orchestratore.py
├── rag_interno.py
│
├── analisi_benford_output.xlsx
├── Report BenfordScan.pdf
├── requirements.txt
├── .gitignore
└── README.md
```

---

## Come eseguire il progetto

Installare le dipendenze:

```powershell
pip install -r requirements.txt
```

Scaricare i modelli Ollama:

```powershell
ollama pull llama3.2
ollama pull bge-m3
```

Eseguire l'analisi Benford:

```powershell
python analisi_benford.py
```

Questo genera:

- `analisi_benford_output.xlsx`
- `data/risultati_benford.txt`

Avviare la demo interattiva:

```powershell
python main.py
```

Opzionale: generare un report testuale tramite agente interpretativo:

```powershell
python agente_benford_opzionale.py
```

---
## Note hardware

Il progetto è stato sviluppato e testato su Windows con Python 3.12.

I modelli vengono eseguiti localmente tramite Ollama. Non è necessaria una GPU dedicata per eseguire la demo, perché il modello `llama3.2` è sufficientemente leggero per questo caso d'uso.

La scelta di usare modelli locali leggeri rende il progetto eseguibile anche su hardware non specializzato e mantiene i dati interni separati dalle fonti esterne.

## Ordine di esecuzione

1. `python analisi_benford.py` — genera Excel e TXT knowledge base
2. `python main.py` — avvia la demo interattiva
3. `python agente_benford_opzionale.py` — opzionale, genera report testuale

---

## Nota sugli embedding

Il file `embeddings/risultati_benford.json` contiene gli embedding della knowledge base `data/risultati_benford.txt`.

Questo file non è incluso nel repository perché viene generato automaticamente alla prima esecuzione di `python main.py`.

Non è necessario eliminarlo a ogni esecuzione. Deve essere cancellato solo se viene modificato il file `risultati_benford.txt`, se cambia il modello di embedding oppure se viene modificata la logica di chunking.

In quel caso, il file può essere eliminato con:

```powershell
del "embeddings\risultati_benford.json"
```

Alla successiva esecuzione di `python main.py`, gli embedding verranno rigenerati automaticamente.

## File principali

### analisi_benford.py

Esegue l'analisi di Benford's Law sul dataset.

Produce:

- un file Excel con risultati, tabelle e grafici;
- un file TXT strutturato usato come knowledge base per il RAG.

### rag_interno.py

Implementa il RAG locale.

Il file:

1. legge il TXT;
2. divide il testo in chunk;
3. genera embedding con `bge-m3`;
4. calcola cosine similarity;
5. recupera i chunk più rilevanti;
6. passa il contesto a `llama3.2`.

### agente_web.py

Implementa un agente web che usa solo fonti pubbliche esterne.

Non ha accesso ai dati interni.

### orchestratore.py

Classifica la domanda in tre categorie:

- `interna`: usa solo il RAG interno;
- `esterna`: usa solo l'agente web;
- `ibrida`: usa RAG interno + agente web.

Nelle query ibride, la domanda viene anonimizzata prima di essere inviata all'agente web.

### main.py

Avvia l'interfaccia interattiva da terminale.

---

## Domande demo

### Domanda interna

```text
Qual è il tasso di frode nel dataset?
```

Risposta attesa:

```text
0.163%
```

### Domanda interna

```text
Quale prefisso presenta la deviazione più alta nelle prime due cifre?
```

Risposta attesa:

```text
Prefisso 10, con scarto frode +23.5 punti percentuali.
```

### Domanda interna

```text
Quale soglia aziendale è critica?
```

Risposta attesa:

```text
La soglia di 100 euro, con tasso di frode 1.05%.
```

### Domanda esterna

```text
Quali sono i trend attuali del card fraud in Europa?
```

Risposta attesa: il sistema classifica la domanda come `ESTERNA` e usa l'agente web per produrre una sintesi dei trend europei da fonti pubbliche, ad esempio PSD2, SCA e card-not-present fraud.

### Domanda ibrida

```text
Le anomalie trovate sono coerenti con i pattern di frode noti nel settore?
```

Risposta attesa: il sistema classifica la domanda come `IBRIDA`, usa il RAG interno per recuperare i risultati Benford e usa l'agente web per confrontarli con trend esterni. Prima della ricerca web, la query viene anonimizzata per evitare l'esposizione dei dati interni.

---

## Risultati principali

I risultati principali dell'analisi sono:

- tasso di frode del dataset: 0.163%;
- anomalia forte sulla prima cifra 1: +14.4 punti percentuali;
- anomalia più forte sulla seconda cifra 0: +21.4 punti percentuali;
- prefisso più anomalo nelle prime due cifre: 10, con +23.5 punti percentuali;
- soglia critica: 100 euro, con tasso frode 1.05%.

L'interpretazione operativa è che le anomalie siano coerenti con un possibile pattern di card testing fraud, perché emergono micro-transazioni, importi tondi e concentrazione sul prefisso 10.

---

## Scelte progettuali

È stato scelto il RAG invece del fine tuning perché i dati e i risultati possono essere aggiornati senza riaddestrare il modello.

Il RAG mantiene la knowledge base in locale, riducendo il rischio di esporre dati interni.

L'orchestratore separa il dominio interno dal dominio esterno.

Quando la query è ibrida, il sistema usa prima il RAG interno e poi anonimizza la domanda prima di inviarla all'agente web.

---

## Limiti del progetto

Benford's Law non dimostra automaticamente la presenza di frode.

Le anomalie sono segnali di rischio e richiedono sempre giudizio professionale.

L'analisi usa solo la colonna `Amount`, perché è l'unica direttamente interpretabile come valore economico. Le colonne `V1-V28` non vengono usate perché sono componenti PCA anonimizzate.

La qualità del RAG dipende dal chunking, dall'embedding model, dalla struttura del documento testuale e dall'aggiornamento della knowledge base `data/risultati_benford.txt`.

La ricerca web dipende dalla qualità dei risultati restituiti dalle fonti pubbliche. Nelle domande ibride, la query viene anonimizzata per ridurre il rischio di esposizione dei dati interni.
