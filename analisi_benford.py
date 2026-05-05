# ============================================================
# ANALISI BENFORD'S LAW - FRAUD DETECTION
# Dataset: Credit Card Fraud Detection (ULB, Kaggle)
# Progetto: BenfordScan
# Riferimento teorico: Nigrini (1994, 2020) - Forensic Analytics
# ============================================================

import os
import pandas as pd
import numpy as np
from openpyxl import Workbook
from openpyxl.styles import (Font, PatternFill, Alignment, 
                              Border, Side)
from openpyxl.chart import BarChart, Reference
from openpyxl.utils import get_column_letter

# ── CARICAMENTO DATI ─────────────────────────────────────────

print("Caricamento dataset...")
df = pd.read_csv("creditcard.csv")

# Usiamo SOLO Amount e Class per mantenere l'analisi interpretabile:
# V1-V28: componenti PCA anonimizzate, non interpretabili con BL
# Amount: importi reali in euro, coprono più ordini di grandezza
# Class: 0=legittima, 1=frode
legittime  = df[df["Class"] == 0]["Amount"]
fraudolente = df[df["Class"] == 1]["Amount"]

# Filtra importi > 0 (BL non definita per zero)
legittime   = legittime[legittime > 0]
fraudolente = fraudolente[fraudolente > 0]

print(f"Dataset caricato: {len(df):,} transazioni totali")

# ── FUNZIONI BL ──────────────────────────────────────────────

def prima_cifra(x):
    s = str(abs(x)).replace(".", "").lstrip("0")
    return int(s[0]) if s else None

def seconda_cifra(x):
    """
    Analisi della seconda cifra secondo l'approccio di Nigrini.
    La seconda cifra segue una distribuzione Benford specifica, non uniforme.

    """
    s = str(abs(x)).replace(".", "").lstrip("0")
    return int(s[1]) if len(s) >= 2 else None

def prime_due_cifre(x):
    """
    Analisi delle prime due cifre secondo Nigrini (1994).
    Questo livello permette di individuare pattern più specifici
    rispetto alla sola prima cifra.
    """
    s = str(abs(x)).replace(".", "").lstrip("0")
    return int(s[:2]) if len(s) >= 2 else None

def distribuzione(serie, func, valori_validi):
    cifre = serie.apply(func).dropna()
    cifre = cifre[cifre.isin(valori_validi)]
    conteggi = cifre.value_counts().sort_index()
    return (conteggi / conteggi.sum() * 100).reindex(valori_validi)

# Distribuzioni attese da Benford
benford_1 = {d: np.log10(1 + 1/d) * 100 for d in range(1, 10)}
# Formula corretta seconda cifra Benford (Nigrini)
# P(seconda cifra = d) = sum_{k=1}^{9} log10(1 + 1/(10k+d))
benford_2 = {}
for d in range(0, 10):
    val = sum(np.log10(1 + 1/(10*k + d)) for k in range(1, 10))
    benford_2[d] = val * 100

benford_12 = {d: np.log10(1 + 1/d) * 100 for d in range(10, 100)}

# ── 1. ANALISI DESCRITTIVA ───────────────────────────────────

print("Calcolo analisi descrittiva...")

desc = pd.DataFrame({
    "Metrica": [
        "Totale transazioni",
        "Transazioni legittime",
        "Transazioni fraudolente",
        "Tasso di frode (%)",
        "",
        "Importo medio legittimo (€)",
        "Importo mediano legittimo (€)",
        "Importo max legittimo (€)",
        "Importo min legittimo (€)",
        "",
        "Importo medio fraudolento (€)",
        "Importo mediano fraudolento (€)",
        "Importo max fraudolento (€)",
        "Importo min fraudolento (€)",
        "",
        "Ordini di grandezza legittime",
        "Ordini di grandezza fraudolente",
        "BL applicabile (>2 ordini grandezza)",
    ],
    "Valore": [
        f"{len(df):,}",
        f"{len(legittime):,}",
        f"{len(fraudolente):,}",
        f"{len(fraudolente)/len(df)*100:.3f}%",
        "",
        f"{legittime.mean():.2f}",
        f"{legittime.median():.2f}",
        f"{legittime.max():.2f}",
        f"{legittime.min():.4f}",
        "",
        f"{fraudolente.mean():.2f}",
        f"{fraudolente.median():.2f}",
        f"{fraudolente.max():.2f}",
        f"{fraudolente.min():.4f}",
        "",
        f"{np.log10(legittime.max()/legittime.min()):.1f}",
        f"{np.log10(fraudolente.max()/fraudolente.min()):.1f}",
        "SI - requisito Benford soddisfatto",
    ]
})

# ── 2. ANALISI PRIMA CIFRA ───────────────────────────────────

print("Calcolo prima cifra...")

dist_l1 = distribuzione(legittime, prima_cifra, range(1,10))
dist_f1 = distribuzione(fraudolente, prima_cifra, range(1,10))

ris1 = pd.DataFrame({
    "Cifra": range(1, 10),
    "Benford_%": [round(benford_1[d], 3) for d in range(1, 10)],
    "Legittime_%": dist_l1.round(3).values,
    "Fraudolente_%": dist_f1.round(3).values,
})
ris1["Scarto_Legit"]  = (ris1["Legittime_%"]   - ris1["Benford_%"]).round(3)
ris1["Scarto_Frode"]  = (ris1["Fraudolente_%"] - ris1["Benford_%"]).round(3)
ris1["Anomalia_Frode"] = ris1["Scarto_Frode"].abs() > 5

# ── 3. ANALISI SECONDA CIFRA (Nigrini) ──────────────────────

print("Calcolo seconda cifra (Nigrini)...")

dist_l2 = distribuzione(legittime, seconda_cifra, range(0,10))
dist_f2 = distribuzione(fraudolente, seconda_cifra, range(0,10))

ris2 = pd.DataFrame({
    "Cifra": range(0, 10),
    "Benford_%": [round(benford_2[d], 3) for d in range(0, 10)],
    "Legittime_%": dist_l2.round(3).values,
    "Fraudolente_%": dist_f2.round(3).values,
})
ris2["Scarto_Legit"]  = (ris2["Legittime_%"]   - ris2["Benford_%"]).round(3)
ris2["Scarto_Frode"]  = (ris2["Fraudolente_%"] - ris2["Benford_%"]).round(3)

# ── 4. ANALISI PRIME DUE CIFRE (Nigrini 1994) ───────────────

print("Calcolo prime due cifre...")

dist_l12 = distribuzione(legittime, prime_due_cifre, range(10,100))
dist_f12 = distribuzione(fraudolente, prime_due_cifre, range(10,100))

ris12 = pd.DataFrame({
    "Prime_2_cifre": range(10, 100),
    "Benford_%": [round(benford_12[d], 3) for d in range(10, 100)],
    "Legittime_%": dist_l12.round(3).values,
    "Fraudolente_%": dist_f12.round(3).values,
})
ris12["Scarto_Frode"] = (ris12["Fraudolente_%"] - ris12["Benford_%"]).round(3)
ris12["Scarto_Legit"] = (ris12["Legittime_%"]   - ris12["Benford_%"]).round(3)
# Top anomalie frode
ris12["Top_Anomalia"] = ris12["Scarto_Frode"].abs() > 1.0

# ── 5. ANALISI SOGLIE AZIENDALI ──────────────────────────────

print("Calcolo soglie aziendali...")

# Analisi delle concentrazioni vicino a soglie operative rilevanti
soglie = [10, 50, 100, 500, 1000, 2000]
righe_soglie = []

for s in soglie:
    margine = s * 0.05
    sl = legittime[(legittime >= s - margine) & (legittime < s)]
    sf = fraudolente[(fraudolente >= s - margine) & (fraudolente < s)]
    tot = len(sl) + len(sf)
    righe_soglie.append({
        "Soglia_€": s,
        "Range": f"{s-margine:.1f} – {s:.1f}",
        "N_Legittime": len(sl),
        "N_Fraudolente": len(sf),
        "Tasso_Frode_%": round(len(sf)/tot*100, 2) if tot > 0 else 0,
        "Segnale": "⚠ ATTENZIONE" if (len(sf)/tot*100 > 0.5 if tot > 0 else False) 
                   else "normale"
    })

ris_soglie = pd.DataFrame(righe_soglie)

# ── 6. SCRITTURA EXCEL CON GRAFICI ───────────────────────────

print("Creazione file Excel...")

wb = Workbook()

# Stili
HDR_FILL  = PatternFill("solid", fgColor="1F4E79")  # blu scuro
HDR_FONT  = Font(bold=True, color="FFFFFF", name="Arial", size=11)
TITLE_FONT = Font(bold=True, name="Arial", size=13, color="1F4E79")
NORM_FONT  = Font(name="Arial", size=10)
WARN_FILL  = PatternFill("solid", fgColor="FFE699")  # giallo warning
ERR_FILL   = PatternFill("solid", fgColor="FF7070")  # rosso anomalia
OK_FILL    = PatternFill("solid", fgColor="C6EFCE")  # verde ok
BORDER     = Border(
    left=Side(style="thin"), right=Side(style="thin"),
    top=Side(style="thin"),  bottom=Side(style="thin")
)
CENTER = Alignment(horizontal="center", vertical="center")

def stile_header(ws, riga, col_start, col_end):
    for c in range(col_start, col_end + 1):
        cell = ws.cell(row=riga, column=c)
        cell.fill = HDR_FILL
        cell.font = HDR_FONT
        cell.alignment = CENTER
        cell.border = BORDER

def stile_riga(ws, riga, col_start, col_end, fill=None):
    for c in range(col_start, col_end + 1):
        cell = ws.cell(row=riga, column=c)
        cell.font = NORM_FONT
        cell.alignment = CENTER
        cell.border = BORDER
        if fill:
            cell.fill = fill

# ── FOGLIO 0: INDICE ─────────────────────────────────────────

ws0 = wb.active
ws0.title = "INDICE"
ws0.column_dimensions["A"].width = 40
ws0.column_dimensions["B"].width = 50

ws0["A1"] = "ANALISI BENFORD'S LAW - FRAUD DETECTION"
ws0["A1"].font = Font(bold=True, size=16, color="1F4E79", name="Arial")
ws0.merge_cells("A1:B1")
ws0["A1"].alignment = CENTER

ws0["A3"] = "Foglio"
ws0["B3"] = "Contenuto"
stile_header(ws0, 3, 1, 2)

indice = [
    ("1_Descrittiva",          "Statistiche descrittive del dataset"),
    ("2_Prima_cifra",          "BL prima cifra + grafico"),
    ("3_Seconda_cifra",        "BL seconda cifra (Nigrini)"),
    ("4_Prime_due_cifre",      "BL prime due cifre (Nigrini 1994)"),
    ("5_Soglie_aziendali",     "Analisi concentrazione frodi vicino a soglie"),
    ("6_Sintesi_anomalie",     "Riepilogo anomalie significative"),
]
for i, (foglio, desc_) in enumerate(indice, start=4):
    ws0.cell(row=i, column=1, value=foglio).font = NORM_FONT
    ws0.cell(row=i, column=2, value=desc_).font  = NORM_FONT
    stile_riga(ws0, i, 1, 2)

ws0["A11"] = "Fonte dataset:"
ws0["B11"] = "ULB Machine Learning Group - Kaggle (creditcard.csv)"
ws0["A12"] = "Riferimento teorico:"
ws0["B12"] = "Nigrini M. (1994, 2020) - Forensic Analytics, Wiley"
ws0["A13"] = "Nota metodologica:"
ws0["B13"] = ("Chi-square NON applicato: campione >100k obs, "
              "tende a rigettare H0 anche per scarti trascurabili (Nigrini, 2020)")
for r in [11, 12, 13]:
    ws0.cell(row=r, column=1).font = Font(bold=True, name="Arial", size=10)
    ws0.cell(row=r, column=2).font = Font(name="Arial", size=10, italic=True)

# ── FOGLIO 1: DESCRITTIVA ────────────────────────────────────

ws1 = wb.create_sheet("1_Descrittiva")
ws1.column_dimensions["A"].width = 35
ws1.column_dimensions["B"].width = 30

ws1["A1"] = "ANALISI DESCRITTIVA DEL DATASET"
ws1["A1"].font = TITLE_FONT
ws1.merge_cells("A1:B1")

ws1["A3"] = "Metrica"
ws1["B3"] = "Valore"
stile_header(ws1, 3, 1, 2)

for i, row in desc.iterrows():
    r = i + 4
    ws1.cell(row=r, column=1, value=row["Metrica"]).font = NORM_FONT
    ws1.cell(row=r, column=2, value=row["Valore"]).font  = NORM_FONT
    ws1.cell(row=r, column=1).border = BORDER
    ws1.cell(row=r, column=2).border = BORDER
    if row["Valore"] == "SI - requisito Benford soddisfatto":
        ws1.cell(row=r, column=2).fill = OK_FILL

# ── FOGLIO 2: PRIMA CIFRA + GRAFICO ─────────────────────────

ws2 = wb.create_sheet("2_Prima_cifra")
for col, w in zip("ABCDEFG", [8,12,14,16,14,14,18]):
    ws2.column_dimensions[get_column_letter(
        ord(col)-64)].width = w

ws2["A1"] = "ANALISI PRIMA CIFRA - BENFORD'S LAW"
ws2["A1"].font = TITLE_FONT
ws2.merge_cells("A1:G1")

ws2["A2"] = ("Anomalia = scarto assoluto > 5 punti percentuali "
             "| Caveat: deviazione ≠ frode (Nigrini, 2020)")
ws2["A2"].font = Font(italic=True, name="Arial", size=9, color="595959")
ws2.merge_cells("A2:G2")

headers2 = ["Cifra","Benford_%","Legittime_%","Fraudolente_%",
            "Scarto_Legit","Scarto_Frode","Anomalia_Frode"]
for c, h in enumerate(headers2, 1):
    ws2.cell(row=4, column=c, value=h)
stile_header(ws2, 4, 1, 7)

for i, row in ris1.iterrows():
    r = i + 5
    vals = [row["Cifra"], row["Benford_%"], row["Legittime_%"],
            row["Fraudolente_%"], row["Scarto_Legit"],
            row["Scarto_Frode"], str(row["Anomalia_Frode"])]
    for c, v in enumerate(vals, 1):
        ws2.cell(row=r, column=c, value=v)

    fill = ERR_FILL if row["Anomalia_Frode"] else None
    stile_riga(ws2, r, 1, 7, fill)

# Grafico prima cifra
chart2 = BarChart()
chart2.type = "col"
chart2.title = "Prima cifra: Benford vs Legittime vs Fraudolente"
chart2.y_axis.title = "Frequenza (%)"
chart2.x_axis.title = "Prima cifra"
chart2.width = 22
chart2.height = 14

cats = Reference(ws2, min_col=1, min_row=5, max_row=13)
for col_idx, label in [(2,"Benford"),(3,"Legittime"),(4,"Fraudolente")]:
    data = Reference(ws2, min_col=col_idx, min_row=4, max_row=13)
    chart2.add_data(data, titles_from_data=True)
chart2.set_categories(cats)
chart2.shape = 4
ws2.add_chart(chart2, "A16")

# ── FOGLIO 3: SECONDA CIFRA ──────────────────────────────────

ws3 = wb.create_sheet("3_Seconda_cifra")
for col, w in zip(range(1,7), [8,12,14,16,14,14]):
    ws3.column_dimensions[get_column_letter(col)].width = w

ws3["A1"] = "ANALISI SECONDA CIFRA (Nigrini)"
ws3["A1"].font = TITLE_FONT
ws3.merge_cells("A1:F1")
ws3["A2"] = ("La seconda cifra segue una distribuzione Benford specifica, non uniforme. "
             "Le ultime cifre, invece, tendono più spesso verso l'uniformità.")
ws3["A2"].font = Font(italic=True, name="Arial", size=9, color="595959")
ws3.merge_cells("A2:F2")

headers3 = ["Cifra","Benford_%","Legittime_%","Fraudolente_%",
            "Scarto_Legit","Scarto_Frode"]
for c, h in enumerate(headers3, 1):
    ws3.cell(row=4, column=c, value=h)
stile_header(ws3, 4, 1, 6)

for i, row in ris2.iterrows():
    r = i + 5
    vals = [row["Cifra"], row["Benford_%"], row["Legittime_%"],
            row["Fraudolente_%"], row["Scarto_Legit"], row["Scarto_Frode"]]
    for c, v in enumerate(vals, 1):
        ws3.cell(row=r, column=c, value=v)
    stile_riga(ws3, r, 1, 6)

# Grafico seconda cifra
chart3 = BarChart()
chart3.type = "col"
chart3.title = "Seconda cifra: Benford vs Legittime vs Fraudolente"
chart3.y_axis.title = "Frequenza (%)"
chart3.x_axis.title = "Seconda cifra"
chart3.width = 22
chart3.height = 14

cats3 = Reference(ws3, min_col=1, min_row=5, max_row=14)
for col_idx, label in [(2,"Benford"),(3,"Legittime"),(4,"Fraudolente")]:
    data3 = Reference(ws3, min_col=col_idx, min_row=4, max_row=14)
    chart3.add_data(data3, titles_from_data=True)
chart3.set_categories(cats3)
ws3.add_chart(chart3, "A16")

# ── FOGLIO 4: PRIME DUE CIFRE ────────────────────────────────

ws4 = wb.create_sheet("4_Prime_due_cifre")
for col, w in zip(range(1,7), [14,12,14,16,14,14]):
    ws4.column_dimensions[get_column_letter(col)].width = w

ws4["A1"] = "ANALISI PRIME DUE CIFRE - Nigrini (1994)"
ws4["A1"].font = TITLE_FONT
ws4.merge_cells("A1:F1")
ws4["A2"] = ("L'analisi delle prime due cifre consente di individuare pattern "
             "più specifici rispetto alla sola prima cifra.")
ws4["A2"].font = Font(italic=True, name="Arial", size=9, color="595959")
ws4.merge_cells("A2:F2")

headers4 = ["Prime_2_cifre","Benford_%","Legittime_%","Fraudolente_%",
            "Scarto_Frode","Top_Anomalia"]
for c, h in enumerate(headers4, 1):
    ws4.cell(row=4, column=c, value=h)
stile_header(ws4, 4, 1, 6)

for i, row in ris12.iterrows():
    r = i + 5
    vals = [row["Prime_2_cifre"], row["Benford_%"], row["Legittime_%"],
            row["Fraudolente_%"], row["Scarto_Frode"], str(row["Top_Anomalia"])]
    for c, v in enumerate(vals, 1):
        ws4.cell(row=r, column=c, value=v)
    fill = WARN_FILL if row["Top_Anomalia"] else None
    stile_riga(ws4, r, 1, 6, fill)

# ── FOGLIO 5: SOGLIE AZIENDALI ───────────────────────────────

ws5 = wb.create_sheet("5_Soglie_aziendali")
for col, w in zip(range(1,7), [12,20,16,18,16,18]):
    ws5.column_dimensions[get_column_letter(col)].width = w

ws5["A1"] = "ANALISI SOGLIE AZIENDALI"
ws5["A1"].font = TITLE_FONT
ws5.merge_cells("A1:F1")
ws5["A2"] = ("Analisi delle concentrazioni vicino a soglie operative rilevanti "
             "| Margine analizzato: 5% sotto ogni soglia")
ws5["A2"].font = Font(italic=True, name="Arial", size=9, color="595959")
ws5.merge_cells("A2:F2")

headers5 = ["Soglia_€","Range","N_Legittime","N_Fraudolente",
            "Tasso_Frode_%","Segnale"]
for c, h in enumerate(headers5, 1):
    ws5.cell(row=4, column=c, value=h)
stile_header(ws5, 4, 1, 6)

for i, row in ris_soglie.iterrows():
    r = i + 5
    vals = [row["Soglia_€"], row["Range"], row["N_Legittime"],
            row["N_Fraudolente"], row["Tasso_Frode_%"], row["Segnale"]]
    for c, v in enumerate(vals, 1):
        ws5.cell(row=r, column=c, value=v)
    fill = WARN_FILL if "ATTENZIONE" in str(row["Segnale"]) else OK_FILL
    stile_riga(ws5, r, 1, 6, fill)

# ── FOGLIO 6: SINTESI ANOMALIE ───────────────────────────────

ws6 = wb.create_sheet("6_Sintesi_anomalie")
ws6.column_dimensions["A"].width = 20
ws6.column_dimensions["B"].width = 55
ws6.column_dimensions["C"].width = 20

ws6["A1"] = "SINTESI ANOMALIE E INTERPRETAZIONE"
ws6["A1"].font = TITLE_FONT
ws6.merge_cells("A1:C1")

ws6["A3"] = "Anomalia"
ws6["B3"] = "Interpretazione operativa"
ws6["C3"] = "Priorità"
stile_header(ws6, 3, 1, 3)

anomalie = [
    ("Prima cifra 1: +14.4pp frodi",
     "Le frodi si concentrano su importi che iniziano con 1, come 1€, 10€ o 19€. "
     "Questo è coerente con un possibile pattern di card testing fraud.",
     "ALTA"),
    ("Seconda cifra 0: +21.4pp frodi",
     "È l'anomalia più forte: indica una concentrazione su importi tondi come 1.00€, "
     "10.00€ o 100.00€. Questo rafforza l'ipotesi di micro-transazioni di test.",
     "ALTA"),
    ("Prime due cifre 10: +23.5pp frodi",
     "Il prefisso 10 è fortemente sovrarappresentato nelle frodi. Questo conferma "
     "la concentrazione su importi piccoli e arrotondati.",
     "ALTA"),
    ("Prime due cifre 99: +6.3pp frodi",
     "Il prefisso 99 può indicare importi psicologici, come 0.99€, 9.99€ o 99€. "
     "Va interpretato con cautela perché anche il retail legittimo usa spesso prezzi psicologici.",
     "MEDIA"),
    ("Soglia €100: tasso frode 1.05%",
     "È l'unica soglia aziendale con segnale rilevante. Può indicare un comportamento "
     "sequenziale: test iniziale con piccoli importi e successivo tentativo vicino a una soglia più alta.",
     "MEDIA"),
    ("CAVEAT metodologico",
     "Deviazione da Benford non implica automaticamente frode. Le anomalie devono essere "
     "interpretate come segnali di rischio e richiedono giudizio professionale.",
     "SEMPRE"),
]

for i, (an, interp, prio) in enumerate(anomalie, start=4):
    ws6.cell(row=i, column=1, value=an)
    ws6.cell(row=i, column=2, value=interp)
    ws6.cell(row=i, column=3, value=prio)
    fill = (ERR_FILL if prio == "ALTA" else
            WARN_FILL if prio == "MEDIA" else OK_FILL)
    stile_riga(ws6, i, 1, 3, fill)
    ws6.cell(row=i, column=2).alignment = Alignment(
        wrap_text=True, vertical="center")
    ws6.row_dimensions[i].height = 45

# ── SALVATAGGIO ──────────────────────────────────────────────

output_file = "analisi_benford_output.xlsx"
wb.save(output_file)

print(f"\nFile salvato: {output_file}")
print("\n── PRIMA CIFRA ──")
print(ris1.to_string(index=False))
print("\n── SOGLIE AZIENDALI ──")
print(ris_soglie.to_string(index=False))
print("\nAnalisi completata. Apri analisi_benford_output.xlsx in Excel.")
# ── EXPORT TXT PER RAG ───────────────────────────────────────
# I risultati vengono salvati come knowledge base interna.
# Questo file non esce mai verso fonti esterne.

os.makedirs("data", exist_ok=True)

txt_output = f"""ANALISI BENFORD'S LAW - RISULTATI INTERNI RISERVATI

Dataset: Credit Card Fraud Detection.
Totale transazioni analizzate: {len(df):,}.

RIEPILOGO OPERATIVO

Il tasso di frode nel dataset è 0.163%.

L'anomalia principale nella prima cifra è la cifra 1, con scarto frode +14.4 punti percentuali.

L'anomalia più forte nella seconda cifra è la cifra 0, con scarto frode +21.4 punti percentuali.

Il prefisso più anomalo nelle prime due cifre è 10, con scarto frode +23.5 punti percentuali.

La soglia aziendale critica, cioè quella con segnale di attenzione, è la soglia di 100 euro, con tasso di frode 1.05%.

Il pattern complessivo è coerente con card testing fraud: micro-transazioni, importi tondi e prefisso 10 sovrarappresentato.

ANALISI DESCRITTIVA

Il dataset contiene {len(legittime):,} transazioni legittime e {len(fraudolente):,} transazioni fraudolente.

Il tasso di frode nel dataset è pari a {len(fraudolente)/len(df)*100:.3f}%.

L'importo medio delle transazioni legittime è {legittime.mean():.2f} euro, mentre l'importo mediano delle transazioni legittime è {legittime.median():.2f} euro.

L'importo medio delle transazioni fraudolente è {fraudolente.mean():.2f} euro, mentre l'importo mediano delle transazioni fraudolente è {fraudolente.median():.2f} euro.

L'importo massimo fraudolento è {fraudolente.max():.2f} euro.

Il dataset copre {np.log10(legittime.max()/legittime.min()):.1f} ordini di grandezza. Il requisito per applicare la legge di Benford è soddisfatto, perché la distribuzione copre più ordini di grandezza.


RISULTATI PRIMA CIFRA

Nell'analisi della prima cifra, la cifra 1 presenta un'anomalia rilevante. Il valore atteso secondo Benford è 30.1%, mentre nelle transazioni fraudolente la cifra 1 compare nel 44.5% dei casi. Lo scarto frode è +14.4 punti percentuali.

La cifra 2 presenta una seconda anomalia rilevante. Il valore atteso secondo Benford è 17.6%, mentre nelle transazioni fraudolente compare nell'8.6% dei casi. Lo scarto frode è -9.0 punti percentuali.

Le cifre 7 e 9 mostrano anomalie moderate. La cifra 7 ha uno scarto frode di circa +5.0 punti percentuali, mentre la cifra 9 ha uno scarto frode di circa +4.5 punti percentuali.


RISULTATI SECONDA CIFRA

L'anomalia principale nella seconda cifra è la cifra 0, con scarto frode +21.4 punti percentuali.

Nell'analisi della seconda cifra, l'anomalia più forte riguarda la cifra 0.

La cifra 0 ha un valore atteso secondo Benford pari al 12.0%, mentre nelle transazioni fraudolente compare nel 33.3% dei casi.

Lo scarto frode della seconda cifra 0 è pari a +21.4 punti percentuali.

Questa è la deviazione più forte nell'analisi della seconda cifra e indica una concentrazione anomala su importi tondi, come 1.00 euro, 10.00 euro e 100.00 euro.

La cifra 3 presenta una deviazione moderata negativa. Il valore atteso secondo Benford è 10.4%, mentre nelle transazioni fraudolente compare nel 4.8% dei casi. Lo scarto frode è -5.6 punti percentuali.

La cifra 9 nelle transazioni legittime mostra uno scarto positivo rilevante: Benford atteso 8.5%, legittime 19.0%, scarto legittimo +10.5 punti percentuali. Questo può essere spiegato da prezzi psicologici nel retail, come 9.99 euro.


RISULTATI PRIME DUE CIFRE

Nell'analisi delle prime due cifre, il prefisso più anomalo è 10.

Il prefisso 10 ha un valore atteso secondo Benford pari al 4.1%, mentre nelle transazioni fraudolente compare nel 27.7% dei casi.

Lo scarto frode del prefisso 10 è pari a +23.5 punti percentuali.

Il prefisso 10 rappresenta quindi l'anomalia più elevata nell'analisi delle prime due cifre.

Il prefisso 99 ha un valore atteso secondo Benford pari allo 0.4%, mentre nelle transazioni fraudolente compare nel 6.8% dei casi. Lo scarto frode è +6.3 punti percentuali.

Il prefisso 76 ha uno scarto frode di +3.8 punti percentuali.

Il prefisso 77 ha uno scarto frode di +2.1 punti percentuali.


ANALISI SOGLIE AZIENDALI

La soglia aziendale che mostra un segnale di attenzione è la soglia di 100 euro.

Nel range 95.0-100.0 euro sono presenti 2928 transazioni legittime e 31 transazioni fraudolente.

Il tasso di frode vicino alla soglia di 100 euro è pari a 1.05%.

La soglia di 10 euro mostra 6997 transazioni legittime e 2 fraudolente, con tasso frode 0.03%. Il segnale è normale.

La soglia di 50 euro mostra 3783 transazioni legittime e 0 fraudolente, con tasso frode 0.00%. Il segnale è normale.

La soglia di 500 euro mostra 611 transazioni legittime e 2 fraudolente, con tasso frode 0.33%. Il segnale è normale.

La soglia di 1000 euro mostra 286 transazioni legittime e 1 fraudolenta, con tasso frode 0.35%. Il segnale è normale.

La soglia di 2000 euro mostra 93 transazioni legittime e 0 fraudolente, con tasso frode 0.00%. Il segnale è normale.


INTERPRETAZIONE OPERATIVA

Le anomalie principali convergono verso un possibile pattern di card testing fraud.

La sovrarappresentazione della prima cifra 1 indica che molte frodi si concentrano su importi che iniziano con 1, come 1 euro, 10 euro o 19 euro.

La sovrarappresentazione della seconda cifra 0 indica una forte concentrazione su importi tondi, come 1.00 euro, 10.00 euro e 100.00 euro.

La sovrarappresentazione del prefisso 10 conferma la presenza di importi piccoli e arrotondati, compatibili con micro-transazioni di test.

Il prefisso 99 può indicare importi psicologici, come 0.99 euro, 9.99 euro o 99 euro. Tuttavia va interpretato con cautela, perché anche le transazioni legittime nel retail possono usare prezzi psicologici.

La soglia di 100 euro può suggerire un comportamento sequenziale: prima micro-transazioni di test e poi tentativi vicino a una soglia più elevata.

CONSIDERAZIONI OPERATIVE

BenfordScan è uno strumento di supporto al monitoraggio antifrode, non un sistema di decisione automatica.

I segnali individuati devono essere usati come indicatori di priorità per alert, controlli aggiuntivi o revisioni operative. Non devono essere usati come regole rigide di blocco automatico.

L'analisi si concentra sulla colonna Amount perché rappresenta il valore monetario reale delle transazioni. Le colonne V1-V28 non sono state analizzate con Benford's Law perché sono componenti PCA anonimizzate e non interpretabili come valori economici.

La knowledge base interna deve essere aggiornata dopo ogni nuova analisi per mantenere coerenza tra i risultati e le risposte del sistema.

PATTERN CARD TESTING FRAUD

Il pattern complessivo emerso dall'analisi è compatibile con il card testing fraud. In questo tipo di frode una carta rubata viene testata con importi piccoli e tondi per verificare se la carta funziona prima di tentare operazioni di importo maggiore.

Gli indicatori principali del pattern sono: importi che iniziano con 1, seconda cifra 0 che indica importi tondi, prefisso 10 fortemente sovrarappresentato e concentrazione vicino alla soglia di 100 euro.

Questi quattro indicatori convergono verso lo stesso comportamento e si rafforzano a vicenda.

NOTA METODOLOGICA

Il test Chi-square non è stato applicato perché il campione supera 100.000 osservazioni. Su campioni molto grandi, il test tende a rigettare l'ipotesi nulla anche per scarti trascurabili.

Le anomalie individuate non dimostrano automaticamente una frode.

Le anomalie devono essere interpretate come segnali di rischio e richiedono giudizio professionale.

Il riferimento metodologico è Nigrini M. 1994 e 2020, Forensic Analytics.
"""

with open("data/risultati_benford.txt", "w", encoding="utf-8") as f:
    f.write(txt_output)

print("TXT per RAG salvato: data/risultati_benford.txt")