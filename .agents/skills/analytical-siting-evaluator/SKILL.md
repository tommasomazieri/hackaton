---
name: analytical-siting-evaluator
description: >-
  Enforces a strictly analytical, data-backed approach for evaluating 
  data-center locations and energy mixes, requiring quantitative verification,
  explicit units, and mathematical optimization formulas.
---

# Analytical Siting Evaluator

## Overview
Questa skill definisce e impone un protocollo operativo basato su dati quantitativi per valutare la fattibilità e la convenienza di siti candidati per data center e la pianificazione del rispettivo mix energetico.

## Regole di Comportamento (Behavioral Rules)
1. **Verifica Quantitativa Obbligatoria**: Ogni affermazione deve essere supportata da dati concreti. Evitare concetti qualitativi vaghi ("conveniente", "sostenibile", "vicino") a favore di parametri misurabili (MW, €/MWh, gCO2/kWh, ms, km).
2. **Normalizzazione delle Unità**: Utilizzare esclusivamente le seguenti unità standardizzate:
   - **Potenza e Carico**: Megawatt ($MW$) o Gigawatt ($GW$)
   - **Prezzi dell'energia**: Euro per Megawattora ($€/MWh$)
   - **Intensità di Carbonio**: Grammi di $CO_2$ equivalente per Chilowattora ($gCO_2/kWh$)
   - **Latenza di rete**: Millisecondi ($ms$)
   - **Distanze geografiche**: Chilometri ($km$) o Metri ($m$)
3. **Attribuzione delle Fonti**: Dichiarare sempre l'origine e l'anno di riferimento dei dati utilizzati (es. *Ember 2025*, *OSM Node ID 12345*, *PyPSA-Eur simulation*).

## Workflow (Procedura di Analisi)

### 1. Valutazione Multicriterio (MCDA)
Per ogni sito candidato, calcolare un punteggio normalizzato ($S_{\text{score}}$) definito come:
$$S_{\text{score}} = w_{\text{costo}} \cdot C_{\text{norm}} + w_{\text{carbonio}} \cdot CO_{2,\text{norm}} + w_{\text{connettività}} \cdot L_{\text{norm}}$$
dove ciascun termine è normalizzato tra 0 (peggiore) e 1 (migliore).

### 2. Tabella dei Dati di Sintesi
Presentare sempre i confronti in tabelle strutturate come la seguente:

| Sito Candidato | Stato / Regione | Costo Stimato (€/MWh) | Intensità Carbonica (gCO2/kWh) | Latenza Fibra (ms) | Distanza Grid (km) | Capacità Rete (MW) | Fonte Dati |
|---|---|---|---|---|---|---|---|
| [Nome Sito] | [Regione] | [Valore] | [Valore] | [Valore] | [Valore] | [Valore] | [Fonte] |

## Errori Comuni da Evitare
- **Uso di Placeholders**: Non inventare valori. Se un dato non è disponibile, indicare esplicitamente l'assenza del dato o effettuare una query mirata tramite gli strumenti del codebase.
- **Mancata indicazione delle unità**: Presentare cifre nude senza specificare se si tratta di €/MWh o €/kWh.
