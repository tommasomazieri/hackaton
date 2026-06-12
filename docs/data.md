# Analisi Dettagliata dei Database e Opportunità Applicative

Questo documento fornisce un'analisi quantitativa dei database disponibili per il progetto **Data-Center Siting & Power (Invertix)**, descrivendo la loro struttura, le informazioni chiave e le opportunità matematiche ed ingegneristiche per integrarle nel nostro motore di siting ed ottimizzazione.

---

## 1. Ember / Our World in Data (OWID) Energy Database

### A. Caratteristiche dei Dati
*   **Formato & Dimensione**: CSV locale (`data/owid-energy-data.csv`), **$15.19 \text{ MB}$**.
*   **Contenuto**: Serie storiche dal 1900 ad oggi (con aggiornamenti annuali e mensili forniti da Ember) su:
    *   Generazione elettrica per paese (in **TWh**) suddivisa per singola fonte (carbone, gas, solare, eolico, nucleare, idroelettrico).
    *   Intensità di carbonio della rete elettrica nazionale (in **$\text{gCO}_2/\text{kWh}$**).
    *   Domanda e consumi totali di elettricità.

### B. Opportunità Applicative
1.  **Filtro di Sostenibilità Assoluta (Hard Constraint)**:
    *   Se l'utente specifica un limite di emissioni massimo (es. $\text{Target}_{\text{CO}2} = 150 \text{ gCO}_2/\text{kWh}$), lo script esclude immediatamente dall'analisi tutti i paesi la cui intensità carbonica media di rete supera tale soglia (es. escludendo Polonia con $\approx 600 \text{ gCO}_2/\text{kWh}$ o Germania con $\approx 380 \text{ gCO}_2/\text{kWh}$, promuovendo Svezia, Norvegia e Francia).
2.  **Calcolo Impronta Carbonica Scope 2**:
    *   Viene utilizzato come base quantitativa per valutare le emissioni del data center allacciato alla rete elettrica (*grid power*):
        $$\text{Emissioni}_{\text{grid}} = P_{\text{DC}} \times 8760 \text{ ore} \times \text{PUE} \times \text{Intensità}_{\text{carbonio}}$$

---

## 2. OpenStreetMap (OSM) via Overpass API

### A. Caratteristiche dei Dati
*   **Formato & Dimensione**: JSON locale (`data/osm_power_infrastructure.json`), **$753 \text{ KB}$** (estratto pilota Lussemburgo, contenente **4978 elementi**).
*   **Contenuto**: Coordinate geografiche lat/lon di:
    *   Linee e cavi di trasmissione elettrica ad alta tensione (`power=line` / `power=cable`) con classi di voltaggio ($\ge 110 \text{ kV}$, $220 \text{ kV}$, $400 \text{ kV}$).
    *   Sottostazioni elettriche di trasformazione (`power=substation`).
    *   Data center esistenti e nodi infrastrutturali principali.

### B. Opportunità Applicative
1.  **Stima Geometrica del CapEx di Allacciamento**:
    *   Il costo per allacciare un data center cresce linearmente con la distanza dalla sottostazione o dalla linea ad alta tensione più vicina ($D_{\text{grid}}$ in km):
        $$\text{CapEx}_{\text{allacciamento}} = D_{\text{grid}} \times \text{Costo}_{\text{linea/km}} + \text{Costo}_{\text{stazione}}$$
        *Esempio*: In Europa, un elettrodotto aereo a 110 kV costa circa **0.5M€ - 1.2M€ per chilometro**. Calcolando la distanza tramite coordinate OSM, possiamo escludere i siti economicamente insostenibili ($D_{\text{grid}} > 5 \text{ km}$).
2.  **Identificazione dei Corridoi di Connettività**:
    *   Mappando i tracciati stradali ed i corridoi tecnologici dove corrono le dorsali di fibra ottica, possiamo scartare le aree prive di backhaul a bassa latenza, garantendo che i candidati abbiano una latenza fibra stimata $\le 10 \text{ ms}$ verso i nodi di interscambio internet (IXP) principali.

---

## 3. PyPSA-Eur Network Data

### A. Caratteristiche dei Dati
*   **Formato**: Modelli e file NetCDF (`.nc`) caricati tramite la libreria Python `pypsa` e `xarray`.
*   **Contenuto**: Topologia dettagliata della rete di trasmissione europea: nodi di borsa elettrica, limiti termici delle linee, e dati storici di congestione ed erogazione.

### B. Opportunità Applicative
1.  **Verifica della Capacità di Rete Dinamica (Substation Headroom)**:
    *   Calcolare se la sottostazione del nodo prescelto ha spazio termico residuo ($H_{\text{sub}}$ in MW) per accogliere il carico del data center ($P_{\text{DC}}$) senza richiedere l'espansione dei trasformatori (che comporterebbe code di allacciamento da **2 a 7 anni**).
2.  **Analisi Predittiva della Congestione della Rete (Curtailment delle PPA)**:
    *   Simulare la congestione sulle linee di trasmissione per determinare la percentuale di energia prodotta da parchi eolici/solari in PPA che andrebbe persa per distacchi forzati (*curtailment*):
        $$\text{Curtailment Rate} = \frac{E_{\text{tagliata}}}{E_{\text{potenziale}}}$$
        Permette di calcolare con precisione l'energia rinnovabile netta effettivamente erogata al data center.

---

## 4. Google AlphaEarth (Satellite Embeddings in GEE)

### A. Caratteristiche dei Dati
*   **Formato & Canale**: Dataset `GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL` in Google Earth Engine. Vettori di embedding a **64 dimensioni** a risoluzione pixel **$10\text{ m}$**.
*   **Contenuto**: Pattern sintetici meteo-climatici, geomorfologici, di temperatura e di irraggiamento solare.

### B. Opportunità Applicative
1.  **Analisi di Idoneità Climatica per il Free-Cooling**:
    *   I sistemi di raffreddamento consumano il **$30\%$** dell'energia totale di un data center. Usando gli embeddings, classifichiamo i pixel con temperature medie annue costantemente basse e bassa umidità. Questo permette di consigliare siti in cui è possibile implementare il *free-cooling diretto* (uso di aria esterna), riducendo il PUE da **1.5 a 1.1** e risparmiando fino al **$25\%$ dei costi energetici totali (OpEx)**.
2.  **Stima del Potenziale Rinnovabile Locale (On-site Capacity Factor)**:
    *   Correlare i vettori di embedding con i fattori di capacità storici ($CF_{\text{solar}}$ ed $CF_{\text{wind}}$) per calcolare la producibilità annua in loco (in **MWh/anno**) di pannelli fotovoltaici o turbine installate sul perimetro del data center.

---

## 5. IEA Energy & AI Reference Specifications

### A. Caratteristiche dei Dati
*   **Formato & Dimensione**: JSON locale (`data/iea_reference_specs.json`), **$671 \text{ B}$**.
*   **Contenuto**: Costanti tecnologiche certificate per data center ed acceleratori IA (PUE medi, TDP GPU Nvidia H100/B200, percentuali di carico IT).

### B. Opportunità Applicative
1.  **Dimensionamento del Carico Totale alla Rete**:
    *   Traduce la taglia computazionale richiesta dall'utente ($P_{\text{compute}}$ in MW) nel reale carico di potenza richiesto alla rete elettrica ($P_{\text{grid}}$), includendo le perdite dei sistemi ausiliari tramite il PUE (Power Usage Effectiveness):
        $$P_{\text{grid}} = P_{\text{compute}} \times \text{PUE}$$
2.  **Ripartizione dei Consumi per l'Ottimizzazione del Mix**:
    *   Fornisce le baseline di consumo orario orizzontale dei server (carico base al 60%) e dei sistemi di condizionamento (carico termico al 30%, variabile in base alla temperatura esterna fornita da AlphaEarth) per impostare il modello di ottimizzazione lineare (LP) del mix energetico.

---

## Tabella Sinottica delle Opportunità di Integrazione

| Database | Input Principale | Metrica Estratta | Funzione nell'Algoritmo | Output per l'Utente |
|---|---|---|---|---|
| **Ember/OWID** | Paese/Zona | $gCO_2/kWh$, Prezzi medi | Filtro emissioni e stima OpEx base | Costo energetico (€/anno) ed Emissioni totali |
| **OSM** | Raggio di ricerca | Distanza $D_{\text{grid}}$, Sottostazioni | Calcolo del CapEx di allacciamento | Costo stimato infrastruttura allacciamento |
| **PyPSA-Eur** | Nodo di rete | Headroom (MW), N-1 security | Validazione fattibilità fisica allacciamento | Livello di congestione e tempi di attesa della rete |
| **AlphaEarth** | Coordinate pixel | Temperatura, Solare/Vento $CF$ | Ottimizzazione PUE (cooling) e On-site Gen | Dimensionamento solare locale ed efficienza PUE |
| **IEA Specs** | Configurazione IT | Profili di carico hardware, PUE | Calcolo dei requisiti di potenza totale | MW totali contrattualizzati richiesti |
