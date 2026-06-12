# Guida di Sviluppo: Integrazione dei Vincoli di Conformità UE (EED, Tassonomia, EnEfG)

Questo documento funge da guida tecnica per gli sviluppatori di **Invertix**. Definisce come le normative dell'Unione Europea in materia di data center debbano essere tradotte in codice nel motore di calcolo (FastAPI backend) e visualizzate nell'interfaccia utente (Streamlit frontend).

---

## 1. Schema Dati e Contratto API (Pydantic Models)

Il backend deve esporre e validare i seguenti campi per garantire la conformità. 

### A. Modello di Input (`SitingRequest`)
Quando l'utente esegue una query di siting, il payload deve contenere:
```python
from pydantic import BaseModel, Field

class SitingRequest(BaseModel):
    pdc_mw: float = Field(
        ..., 
        gt=0.0, 
        description="Potenza nominale dell'infrastruttura IT del data center in MW"
    )
    footprint_m2: float = Field(
        ..., 
        gt=0.0, 
        description="Superficie coperta totale della sala computer in metri quadrati"
    )
    cooling_type: str = Field(
        "free-cooling", 
        description="Tipologia di condizionamento (free-cooling, evaporative, chilled-water)"
    )
```

### B. Modello di Output di Compliance (`ComplianceScore`)
Il payload di risposta per ogni sito candidato deve includere il seguente blocco di conformità:
```python
from enum import Enum
from typing import List, Optional

class EEDStatus(str, Enum):
    MANDATORY = "MANDATORY"
    VOLUNTARY = "VOLUNTARY"

class EUSizeCategory(str, Enum):
    VERY_SMALL = "Very Small (100-500 kW)"
    SMALL = "Small (500 kW - 1 MW)"
    MEDIUM = "Medium (1 - 2 MW)"
    LARGE = "Large (2 - 10 MW)"
    VERY_LARGE = "Very Large (> 10 MW)"

class TaxonomyStatus(str, Enum):
    ALIGNED = "TAXONOMY ALIGNED"
    NON_ALIGNED = "COMPLIANCE RISK (NON-ALIGNED)"

class ComplianceScore(BaseModel):
    eed_status: EEDStatus
    size_category: EUSizeCategory
    pue_predicted: float
    wue_predicted: float
    erf_predicted: float
    taxonomy_alignment: TaxonomyStatus
    alerts: List[str]
```

---

## 2. Logica Computazionale e Formule (Backend Backend Siting Engine)

Lo sviluppatore deve implementare le seguenti funzioni nel modulo di scoring (es. `src/scoring/compliance.py`):

### A. Classificazione e Obbligo EED
La soglia critica stabilita dalla direttiva EED recast è **$500\text{ kW}$ ($0.5\text{ MW}$)**.
```python
def evaluate_eed_status(pdc_mw: float) -> tuple[EEDStatus, EUSizeCategory]:
    # 1. Determina l'obbligo di report
    status = EEDStatus.MANDATORY if pdc_mw >= 0.5 else EEDStatus.VOLUNTARY
    
    # 2. Assegna la classe dimensionale (Allegato IV)
    if pdc_mw < 0.5:
        category = EUSizeCategory.VERY_SMALL
    elif pdc_mw < 1.0:
        category = EUSizeCategory.SMALL
    elif pdc_mw < 2.0:
        category = EUSizeCategory.MEDIUM
    elif pdc_mw < 10.0:
        category = EUSizeCategory.LARGE
    else:
        category = EUSizeCategory.VERY_LARGE
        
    return status, category
```

### B. Verifica del PUE Limite (Tassonomia e Legge Tedesca EnEfG)
Il limite per i nuovi data center è **$\text{PUE} \le 1.30$**.
*   **Formula di calcolo del PUE di sito**:
    $$\text{PUE}_{\text{predicted}} = 1.05 + 0.25 \times \Phi(T_{\text{wet-bulb}}, \text{cooling\_type})$$
    *Dove $\Phi$ è una funzione di regressione che mappa la temperatura di bulbo umido oraria media locale estratta da AlphaEarth.*
*   **Verifica di Conformità**:
```python
def check_pue_compliance(pue_pred: float) -> tuple[TaxonomyStatus, List[str]]:
    alerts = []
    if pue_pred <= 1.30:
        status = TaxonomyStatus.ALIGNED
    else:
        status = TaxonomyStatus.NON_ALIGNED
        alerts.append(
            f"Il PUE stimato ({pue_pred:.2f}) supera la soglia di compliance di 1.30. "
            "Il sito rischia di non qualificarsi per finanziamenti verdi (Tassonomia UE) "
            "e viola i limiti del German Energy Efficiency Act (EnEfG)."
        )
    return status, alerts
```

### C. Analisi Spaziale del Calore di Scarto (ERF - Energy Reuse Factor)
Se il data center supera $1\text{ MW}$, la legge richiede la predisposizione al recupero termico.
*   **Logica Geospaziale (OSM)**:
    Il backend interroga la cache geospaziale locale (GeoParquet) per calcolare la distanza minima dal nodo $n$ a una infrastruttura di calore (teleriscaldamento o utenza industriale).
```python
def estimate_erf_potential(node_coords: tuple[float, float], pdc_mw: float, osm_data) -> tuple[float, List[str]]:
    alerts = []
    # Cerca nel database OSM elementi taggati come 'steam=pipe', 'utility=heating', o 'industrial'
    dist_to_heat_sink_km = calculate_min_distance_to_heat_sink(node_coords, osm_data)
    
    if dist_to_heat_sink_km <= 2.0:
        # Se c'è un'utenza entro 2km, ipotizziamo un potenziale di recupero ottimale
        erf_pred = 0.20  # 20% ERF
    else:
        erf_pred = 0.0
        if pdc_mw >= 1.0:
            alerts.append(
                f"Assenza di utenze termiche entro 2 km (Distanza: {dist_to_heat_sink_km:.1f} km). "
                "Per impianti >= 1 MW questo comporta una violazione dei requisiti di "
                "Waste Heat Readiness e azzera il punteggio di Energy Reuse Factor (ERF)."
            )
    return erf_pred, alerts
```

### D. Limitazione del Consumo Idrico (WUE Target)
La soglia stabilita dal Climate Neutral Data Centre Pact è **$\text{WUE} \le 0.4 \text{ L/kWh}$**.
```python
def check_wue_compliance(wue_pred: float) -> List[str]:
    alerts = []
    if wue_pred > 0.4:
        alerts.append(
            f"Il consumo d'acqua previsto ({wue_pred:.2f} L/kWh) supera l'obiettivo di "
            "0.4 L/kWh del Climate Neutral Data Centre Pact. Rischio di stress idrico locale."
        )
    return alerts
```

---

## 3. Test Unitari per il Controllo Qualità (QA/QC Assertions)

Gli sviluppatori devono includere i seguenti casi di test in `tests/test_compliance.py` per garantire che i vincoli di classificazione e allineamento funzionino correttamente prima di andare in produzione:

```python
import pytest
from src.scoring.compliance import evaluate_eed_status, check_pue_compliance

def test_eed_threshold_mandatory():
    # Un DC da 600 kW deve essere Mandatory
    status, category = evaluate_eed_status(0.6)
    assert status == "MANDATORY"
    assert category == "Small (500 kW - 1 MW)"

def test_eed_threshold_voluntary():
    # Un DC da 200 kW deve essere Voluntary
    status, category = evaluate_eed_status(0.2)
    assert status == "VOLUNTARY"
    assert category == "Very Small (100-500 kW)"

def test_taxonomy_alignment_success():
    # PUE di 1.20 deve essere Taxonomy Aligned
    status, alerts = check_pue_compliance(1.20)
    assert status == "TAXONOMY ALIGNED"
    assert len(alerts) == 0

def test_taxonomy_alignment_failure():
    # PUE di 1.35 deve fallire l'allineamento e generare un alert
    status, alerts = check_pue_compliance(1.35)
    assert status == "COMPLIANCE RISK (NON-ALIGNED)"
    assert any("supera la soglia di compliance di 1.30" in a for a in alerts)
```

---

## 4. UI Guidelines (Streamlit Frontend)

Per garantire che Jordan (il nostro utente finale) e l'ESG Officer possano leggere immediatamente lo stato di conformità del sito, l'interfaccia Streamlit deve:
1.  **Compliance Badges**: Mostrare dei badge colorati per ciascun sito candidato:
    *   `TAXONOMY ALIGNED` $\rightarrow$ **Verde**
    *   `COMPLIANCE RISK (NON-ALIGNED)` $\rightarrow$ **Rosso**
2.  **EED Warning Card**: Se il data center supera i 500 kW, mostrare un box informativo:
    > [!IMPORTANT]
    > **Impianto a Regime di Reporting Obbligatorio (EED)**
    > Questo impianto supera la soglia di 500 kW. I dati di esercizio (PUE, WUE, ERF) dovranno essere trasmessi annualmente alla banca dati europea a partire dal 15 Agosto 2027.
3.  **Alerts Panel**: Mostrare in un accordion espandibile tutti gli avvisi generati dall'algoritmo (es. mancanza di teleriscaldamento per impianti $\ge 1\text{ MW}$ o superamento del target di consumo idrico).
