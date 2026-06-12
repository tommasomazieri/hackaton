# Analisi Dettagliata dei Database e Opportunità Applicative

Questo documento fornisce un'analisi quantitativa dei database disponibili per il progetto **Data-Center Siting & Power (Invertix)**, descrivendo la loro struttura, la granularità spaziale e temporale, le informazioni chiave e le opportunità matematiche ed ingegneristiche per integrarle nel nostro motore di siting ed ottimizzazione.

---

## 1. Ember / Our World in Data (OWID) Energy Database

### A. Caratteristiche dei Dati
*   **Formato & Dimensione**: CSV locale (`data/owid-energy-data.csv`), **$15.19 \text{ MB}$**.
*   **Granularità Spaziale**: **Nazionale** (livello di Paese o singola zona di mercato elettrico per i prezzi).
*   **Granularità Temporale**: **Annuale e Mensile** (con dati storici aggregati dal 1900 al 2025).
*   **Contenuto**:
    *   Generazione elettrica per paese (in **TWh**) suddivisa per singola fonte (carbone, gas, solare, eolico, nucleare, idroelettrico).
    *   Intensità di carbonio della rete elettrica nazionale (in **$\text{gCO}_2/\text{kWh}$**).
        > [!NOTE]
        > **Definizione di Intensità di Carbonio della Rete**: Rappresenta la massa di anidride carbonica equivalente ($CO_2e$) emessa per ogni unità di energia elettrica generata o consumata. L'unità di misura standard è il grammo di $CO_2$ equivalente per chilowattora ($gCO_2e/kWh$) o il chilogrammo per megawattora ($kgCO_2e/MWh$).
        > 
        > La formula generale di calcolo è:
        > $$\text{CI} = \frac{\sum (E_i \times EF_i)}{\sum E_i}$$
        > Dove $E_i$ è l'energia generata dalla fonte $i$ (in **MWh**) ed $EF_i$ è il fattore di emissione specifico per quella tecnologia (in **$kgCO_2e/MWh$**):
        > - **Carbone**: $\approx 800 - 1000 \text{ gCO}_2/\text{kWh}$
        > - **Gas Naturale**: $\approx 350 - 450 \text{ gCO}_2/\text{kWh}$
        > - **Solare / Eolico (Ciclo di vita)**: $\approx 10 - 40 \text{ gCO}_2/\text{kWh}$
        > - **Nucleare**: $\approx 5 - 12 \text{ gCO}_2/\text{kWh}$
        > 
        > Si distingue inoltre tra:
        > 1. **Generation-based**: Calcolata solo sulla base delle centrali attive nel territorio nazionale.
        > 2. **Consumption-based (raccomandata per il Siting)**: Tiene conto dell'import/export transfrontaliero di energia, calcolando l'effettiva intensità del mix energetico consumato in loco.
    *   Domanda e consumi totali di elettricità.

### B. Opportunità Applicative
1.  **Filtro di Sostenibilità Assoluta (Hard Constraint)**:
    *   Se l'utente specifica un limite di emissioni massimo (es. $\text{Target}_{\text{CO}2} = 150 \text{ gCO}_2/\text{kWh}$), lo script esclude immediatamente dall'analisi tutti i paesi la cui intensità carbonica media di rete supera tale soglia (es. escludendo Polonia con $\approx 600 \text{ gCO}_2/\text{kWh}$ o Germania con $\approx 380 \text{ gCO}_2/\text{kWh}$, promuovendo Svezia, Norvegia e Francia).
2.  **Calcolo Impronta Carbonica Scope 2 (Compliance & Reporting)**:
    *   Viene utilizzato come base quantitativa per valutare le emissioni del data center allacciato alla rete elettrica (*grid power*):
        $$\text{Emissioni}_{\text{grid}} = P_{\text{DC}} \times 8760 \text{ ore} \times \text{PUE} \times \text{Intensità}_{\text{carbonio}}$$
3.  **Ottimizzazione del Dimensionamento delle Batterie (BESS)**:
    *   Un limite rigido di emissioni orarie obbliga a installare sistemi di accumulo a batteria localizzati (BESS) per immagazzinare energia pulita quando l'intensità della griglia è bassa, rilasciandola durante le ore di picco fossile della rete. Il target di emissioni definisce direttamente la capacità di stoccaggio minima (in **MWh**) per garantire la continuità energetica senza violare il vincolo carbonico.
4.  **Carbon-Aware Load Shifting (Spaziale e Temporale)**:
    *   Il target $Target_{CO2}$ abilita algoritmi di flessibilizzazione del carico IT. Se l'intensità locale supera la soglia in una certa ora $t$, i carichi computazionali non urgenti (es. training di LLM) vengono posticipati o migrati via cloud in altri nodi geografici europei con rete temporaneamente più verde (es. Svezia):
        $$\text{Carico}(t) = \begin{cases} P_{\text{max}} & \text{se } \text{Intensity}(t) \le \text{Target}_{\text{CO}2} \\ P_{\text{baseline}} & \text{se } \text{Intensity}(t) > \text{Target}_{\text{CO}2} \end{cases}$$
5.  **Accesso a Green Financing e Riduzione Carbon Tax**:
    *   Il rispetto di un target inferiore a **$100\text{ gCO}_2/\text{kWh}$** allinea il data center con i criteri della Tassonomia UE per la Finanza Sostenibile. Questo permette alla società di accedere a finanziamenti agevolati (*Green Bonds*) con una riduzione dei tassi di interesse stimata tra **50 e 150 punti base (0.5% - 1.5%)**, oltre a evitare i costi legati alla tassazione del carbonio (ETS) nei mercati regolamentati.

---

## 2. OpenStreetMap (OSM) via Overpass API

### A. Caratteristiche dei Dati
*   **Formato & Dimensione**: JSON locale (`data/osm_power_infrastructure.json`), **$753 \text{ KB}$** (estratto pilota Lussemburgo, contenente **4978 elementi**).
*   **Granularità Spaziale**: **Sub-metrica / Vettoriale** (coordinate geografiche precise in latitudine e longitudine di nodi e linee).
*   **Granularità Temporale**: **Statica** (corrisponde all'ultimo snapshot del database al momento del download).
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
*   **Granularità Spaziale**: **Nodale (Nodal-level)**. I dati sono associati ai singoli nodi di rete (sottostazioni ad altissima tensione della rete di trasmissione ENTSO-E, solitamente distanziate di **20–80 km**).
*   **Granularità Temporale**: **Oraria ($1\text{ ora}$)** per un intero anno storico ($8760\text{ ore}$ totali).
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
*   **Formato & Canale**: Dataset `GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL` in Google Earth Engine.
*   **Granularità Spaziale**: **Pixel-level ad altissima risoluzione ($10\text{ m} \times 10\text{ m}$)**.
*   **Granularità Temporale**: **Annuale** (serie di immagini composte annuali dal 2017 al 2024).
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
*   **Granularità Spaziale**: **Nessuna (Globale/Tecnologico)**. I dati rappresentano costanti costruttive e benchmark di settore.
*   **Granularità Temporale**: **Nessuna (Statica)**. Rappresenta stime medie per il periodo 2025/2026.
*   **Contenuto**: Costanti tecnologiche certificate per data center ed acceleratori IA (PUE medi, TDP GPU Nvidia H100/B200, percentuali di carico IT).

### B. Opportunità Applicative
1.  **Dimensionamento del Carico Totale alla Rete**:
    *   Traduce la taglia computazionale richiesta dall'utente ($P_{\text{compute}}$ in MW) nel reale carico di potenza richiesto alla rete elettrica ($P_{\text{grid}}$), includendo le perdite dei sistemi ausiliari tramite il PUE (Power Usage Effectiveness):
        $$P_{\text{grid}} = P_{\text{compute}} \times \text{PUE}$$
2.  **Ripartizione dei Consumi per l'Ottimizzazione del Mix**:
    *   Fornisce le baseline di consumo orario orizzontale dei server (carico base al 60%) e dei sistemi di condizionamento (carico termico al 30%, variabile in base alla temperatura esterna fornita da AlphaEarth) per impostare il modello di ottimizzazione lineare (LP) del mix energetico.

---

## 6. Analisi dei Mismatch di Granularità e Impatti sul Progetto

L'integrazione di questi cinque database presenta significative discrepanze di risoluzione spaziale e temporale. Di seguito si analizzano i principali mismatch e le strategie matematiche/ingegneristiche per mitigarne l'impatto.

### A. Mismatch Spaziale (da Nazionale a Pixel-level)
*   **La Discrepanza**: Ember/OWID fornisce i dati sul carbonio e sul mix energetico a livello **nazionale** (es. l'intera Germania), mentre PyPSA-Eur opera a livello **nodale** (aree di 50 km) e OSM/AlphaEarth scendono a livello **metrico/pixel** ($10\text{ m}$).
*   **Gli Impatti**:
    *   *Sottostima delle emissioni locali*: L'intensità di carbonio reale varia significativamente all'interno di una nazione in base alla congestione della rete interna (es. la Germania del Nord ha surplus eolico a basso carbonio, mentre la Germania del Sud brucia più carbone a causa dei limiti di trasmissione nord-sud). Assumere il valore medio nazionale di Ember introduce un errore stimato del **10-30%** sulle emissioni effettive del data center.
    *   *Complessità Computazionale*: Lo screening geospaziale dell'intera Europa alla risoluzione di $10\text{ m}$ di AlphaEarth è impossibile in tempo reale ($>1.5\text{ miliardi di pixel}$).
*   **Strategia di Mitigazione (Approccio Gerarchico)**:
    1.  *Filtro 1 (Nazionale - Ember)*: Escludere nazioni con normative energetiche non idonee o prezzi medi fuori budget.
    2.  *Filtro 2 (Nodale - PyPSA/OSM)*: Effettuare la simulazione dinamica sui soli nodi di trasmissione superstiti per verificare la capacità termica.
    3.  *Filtro 3 (Micro-Siting - AlphaEarth)*: Solo per i top 5 nodi consigliati, analizzare un buffer geospaziale di $1\text{ km} \times 1\text{ km}$ a risoluzione di $10\text{ m}$ per ottimizzare il posizionamento esatto dei pannelli solari ed evitare zone a rischio idrogeologico.

### B. Mismatch Temporale (da Statico a Orario)
*   **La Discrepanza**: I dati di Ember/OWID sono aggregati annualmente o mensilmente. OSM e IEA sono istantanei/statici. PyPSA-Eur, al contrario, necessita di simulazioni **orarie** ($8760\text{ passi}$).
*   **Gli Impatti**:
    *   *Errore nel dimensionamento delle batterie (On-site Storage)*: Se ottimizziamo il mix energetico basandoci solo sull'irraggiamento solare annuale o mensile medio, rischiamo di sottostimare la necessità di accumulo. Un data center richiede potenza costante $24/7$, mentre l'energia solare locale crolla a $0\text{ MW}$ di notte. Utilizzare medie temporali aggregate porta a proporre batterie sottodimensionate del **$40\text{-}60\%$**, costringendo il data center ad acquistare energia dalla rete nei picchi di costo.
*   **Strategia di Mitigazione (Sintesi di Profili Orari)**:
    *   Utilizziamo i dati storici annuali/mensili di Ember e AlphaEarth come **fattori di scala** per calibrare profili sintetici orari standard generati tramite modelli climatici o librerie come `pvlib`. Ad esempio, normalizziamo il solar capacity factor ricavato da AlphaEarth su un profilo sinusoidale orario giornaliero interpolato con le ore di luce solare storiche della latitudine del sito.

---

## Tabella Sinottica delle Granularità

| Database | Granularità Spaziale | Granularità Temporale | Variabile Chiave Gestita | Rischio di Mismatch |
|---|---|---|---|---|
| **Ember/OWID** | Nazionale | Annuale / Mensile | $\text{gCO}_2/\text{kWh}$, Prezzi | Sottostima della variazione locale del carbonio |
| **OSM** | Vettoriale (Sub-metrica) | Statica | Posizione dei cavi e sottostazioni | Variazioni future della rete non mappate |
| **PyPSA-Eur** | Nodale ($20\text{-}80\text{ km}$) | Oraria ($1\text{ ora}$) | Flusso di carico (MW), Prezzo zonale | Complessità di calcolo per simulazioni di massa |
| **AlphaEarth** | Pixel ($10\text{ m}$) | Annuale (Composita) | Temperatura locale, Irraggiamento | Assenza di andamenti meteorologici orari estremi |
| **IEA Specs** | Globale | Statica | Costanti PUE, TDP hardware | Rapida obsolescenza tecnologica dell'hardware |

---

## Tabella Sinottica delle Opportunità di Integrazione

| Database | Input Principale | Metrica Estratta | Funzione nell'Algoritmo | Output per l'Utente |
|---|---|---|---|---|
| **Ember/OWID** | Paese/Zona | $gCO_2/kWh$, Prezzi medi | Filtro emissioni e stima OpEx base | Costo energetico (€/anno) ed Emissioni totali |
| **OSM** | Raggio di ricerca | Distanza $D_{\text{grid}}$, Sottostazioni | Calcolo del CapEx di allacciamento | Costo stimato infrastruttura allacciamento |
| **PyPSA-Eur** | Nodo di rete | Headroom (MW), N-1 security | Validazione fattibilità fisica allacciamento | Livello di congestione e tempi di attesa della rete |
| **AlphaEarth** | Coordinate pixel | Temperatura, Solare/Vento $CF$ | Ottimizzazione PUE (cooling) e On-site Gen | Dimensionamento solare locale ed efficienza PUE |
| **IEA Specs** | Configurazione IT | Profili di carico hardware, PUE | Calcolo dei requisiti di potenza totale | MW totali contrattualizzati richiesti |
