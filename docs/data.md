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

### A. Caratteristiche dei Dati e Struttura delle Componenti
Il database PyPSA-Eur modella la rete di trasmissione ad alta tensione europea (ENTSO-E) integrando sia parametri fisici (costruttivi/statici) sia dinamici (profili temporali e risultati di simulazioni di flusso ottimo di potenza - OPF). 

I dati si strutturano in **Variabili Statiche (Input Fisici)**, **Variabili Temporali di Input (Time Series)** e **Variabili di Output (Risultati dell'OPF)** su base **oraria ($8760\text{ ore}$)**.

#### 1. Nodi (Buses)
Rappresentano le sottostazioni elettriche ad altissima tensione ($\ge 110\text{ kV}$).
*   **Dati Statici**:
    *   `v_nom`: Tensione nominale della sottostazione (in $\text{kV}$, tipicamente $220\text{ kV}$ o $380\text{ kV}$ in Europa).
    *   `x`, `y`: Coordinate geografiche (Longitudine, Latitudine) utilizzate per il georeferenziazione e il micro-siting.
    *   `country`: Codice paese a livello nazionale/NUTS0 (es. `DE`, `FR`, `IT`) utile per l'accoppiamento con i dati di Ember.
    *   `control`: Tipo di nodo per il flusso di carico (Slack, PV, o PQ).
*   **Dati Temporali / Output**:
    *   `marginal_price` (LMP - Locational Marginal Price in $\text{€/MWh}$): Prezzo marginale zonale dell'energia elettrica calcolato orariamente per ciascun nodo. Riflette il costo di generazione orario, le perdite attive di rete e il costo della congestione sulle linee di trasmissione.
    *   `v_mag_pu`: Magnitudo della tensione in per-unit (adimensionale). Indica la stabilità di tensione del nodo (deve rimanere tra $0.95$ e $1.05\text{ pu}$).

#### 2. Linee di Trasmissione (Lines) e Link DC (Links)
Rappresentano gli elettrodotti aerei in corrente alternata (AC) e i cavi di interconnessione sottomarini o inter-zonali in corrente continua (HVDC).
*   **Linee AC (Lines) - Dati Statici**:
    *   `bus0`, `bus1`: Nodi di origine e destinazione della linea.
    *   `s_nom`: Capacità di trasporto termico nominale (limite di flusso continuo in $\text{MVA}$).
    *   `length`: Lunghezza fisica della linea (in $\text{km}$).
    *   `r`, `x`: Resistenza e reattanza elettrica equivalente (in per-unit o $\Omega$), necessarie per il calcolo delle perdite e dei flussi di rete.
    *   `num_parallel`: Numero di circuiti paralleli sulla stessa linea fisica.
*   **Link HVDC (Links) - Dati Statici**:
    *   `bus0`, `bus1`: Nodi di connessione.
    *   `p_nom`: Capacità massima di trasporto di potenza attiva (in $\text{MW}$).
    *   `efficiency`: Efficienza di conversione/trasmissione (adimensionale, es. $0.97$ per considerare il $3\%$ di perdite di conversione AC/DC).
*   **Dati Temporali / Output (Lines & Links)**:
    *   `p0`, `p1`: Flussi orari di potenza attiva transitanti sui due terminali della linea (in $\text{MW}$), positivi se fluiscono da `bus0` a `bus1`.
    *   `q0`, `q1`: Flussi orari di potenza reattiva (in $\text{MVAr}$, solo per linee AC).
    *   `congestione`: Rapporto percentuale istantaneo tra il flusso reale e la capacità limite termica:
        $$\text{LoadRate}(t) = \frac{|P(t)|}{S_{\text{nom}}} \times 100\%$$

#### 3. Generatori (Generators)
Rappresentano gli impianti di produzione di energia allacciati direttamente alla rete di trasmissione.
*   **Dati Statici**:
    *   `p_nom`: Capacità nominale installata del generatore (in $\text{MW}$).
    *   `carrier`: Tecnologia/Vettore energetico. Include: `wind_onshore`, `wind_offshore`, `solar`, `nuclear`, `lignite` (lignite), `coal` (carbon fossile), `gas` (gas naturale), `hydro` (idroelettrico a bacino), `ror` (idroelettrico ad acqua scorrente), `biomass` (biomasse), `oil` (petrolio).
    *   `marginal_cost`: Costo marginale di produzione (in $\text{€/MWh}$), comprensivo di costi del combustibile, efficienza termica e quote di emissione $CO_2$ (ETS).
    *   `capital_cost`: Costo annualizzato dell'investimento per unità di potenza (in $\text{€/MW}\cdot\text{anno}$).
    *   `efficiency`: Efficienza termodinamica del generatore.
*   **Dati Temporali / Output**:
    *   `p_max_pu`: Profilo orario normalizzato ($0\text{-}1$) di producibilità per solare ed eolico basato su rianalisi meteorologiche storiche (reali fattori di capacità orari del sito).
    *   `p`: Generazione elettrica effettiva programmata dall'OPF (in $\text{MW}$).

#### 4. Unità di Accumulo (Storage Units & Stores)
Rappresentano gli impianti idroelettrici a pompaggio (PHS) e i sistemi di accumulo elettrochimico (batterie BESS).
*   **Dati Statici**:
    *   `p_nom`: Potenza nominale del convertitore/inverter (in $\text{MW}$).
    *   `max_hours`: Durata massima dell'accumulo a piena potenza (in $\text{ore}$). Definisce la capacità energetica nominale:
        $$E_{\text{nom}} = P_{\text{nom}} \times \text{max\_hours} \quad (\text{MWh})$$
    *   `efficiency_store` / `efficiency_dispatch`: Rendimento di carica e scarica dell'accumulo (es. $0.90$ per batterie a ioni di litio).
    *   `standing_loss`: Tasso orario di autoscarica del sistema di accumulo.
*   **Dati Temporali / Output**:
    *   `state_of_charge`: Stato di carica istantaneo dell'accumulo (in $\text{MWh}$ per ciascuna delle $8760\text{ ore}$).
    *   `p`: Potenza attiva scambiata con la rete (positiva in fase di scarica, negativa in fase di carica).

#### 5. Trasformatori (Transformers)
Componenti che collegano livelli diversi di tensione (es. accoppiamento $380\text{ kV} / 220\text{ kV}$).
*   **Dati Statici**:
    *   `s_nom`: Capacità nominale del trasformatore (in $\text{MVA}$).
    *   `r`, `x`: Parametri di impedenza interna.

---

### B. Opportunità Applicative e Formule Chiave

1.  **Stima Dinamica del Margine di Capacità (Substation & Node Headroom)**:
    Il posizionamento del data center richiede una sottostazione con sufficiente "headroom" (capacità residua) per evitare costosi e lunghi lavori di potenziamento della griglia (che possono richiedere da $2$ a $7$ anni). Calcoliamo la capacità residua oraria del nodo $n$ all'ora $t$:
    $$H_n(t) = S_{\text{nom, trasformatore}} - P_{\text{load, } n}(t) \quad (\text{MW})$$
    Il headroom minimo annuale indica la taglia massima del data center installabile senza modifiche strutturali:
    $$\text{Headroom}_{\text{static}} = \min_{t} H_n(t)$$
    Per valutare l'impatto dinamico della congestione sulle linee adiacenti al nodo $n$:
    $$\text{Headroom}_{\text{linee}}(n, t) = \min_{l \in \text{Lines}(n)} \left( S_{\text{nom}, l} - |P_l(t)| \right) \quad (\text{MW})$$
    
2.  **Calcolo del Curtailment Rate per le PPA Rinnovabili**:
    Un data center che stipula un accordo PPA (Power Purchase Agreement) per energia eolica o solare situata in un nodo distante rischia che parte dell'energia venga persa causa congestione di rete (*curtailment*). PyPSA ci permette di calcolare il tasso orario di curtailment per un impianto:
    $$\text{Curtailment}(t) = P_{\text{max, pu}}(t) \cdot P_{\text{nom}} - P(t) \quad (\text{MW})$$
    $$\text{Curtailment Rate} = \frac{\sum_{t=1}^{8760} \left[ P_{\text{max, pu}}(t) \cdot P_{\text{nom}} - P(t) \right]}{\sum_{t=1}^{8760} P_{\text{max, pu}}(t) \cdot P_{\text{nom}}} \times 100\%$$
    Questo tasso incide direttamente sul costo reale dell'energia PPA, poiché l'energia non consegnata rappresenta un costo netto non compensato.

3.  **Tracciamento Fisico delle Emissioni a Livello Nodale (Carbon Flow Tracking)**:
    Invece di utilizzare le medie di emissione nazionali statiche di Ember, possiamo sfruttare i flussi orari di potenza di PyPSA per tracciare fisicamente la provenienza degli elettroni consumati al nodo del data center.
    Sia $\text{CI}_n(t)$ l'intensità di carbonio reale del mix consumato al nodo $n$ all'ora $t$. Questa è definita dal bilancio tra la generazione locale al nodo e i flussi di importazione dai nodi vicini:
    $$\text{CI}_n(t) = \frac{\sum_{g \in \text{Gen}_n} G_{g,n}(t) \cdot EF_g + \sum_{m \in \text{Neighbors}_n} F_{mn}(t) \cdot \text{CI}_m(t)}{\sum_{g \in \text{Gen}_n} G_{g,n}(t) + \sum_{m \in \text{Neighbors}_n} F_{mn}(t)} \quad \left(\text{gCO}_2/\text{kWh}\right)$$
    Dove:
    *   $G_{g,n}(t)$ è la generazione oraria del generatore locale $g$ al nodo $n$ (in $\text{MW}$).
    *   $EF_g$ è il fattore di emissione di ciclo di vita specifico del vettore del generatore $g$ (es. $EF_{\text{coal}} = 950\text{ g/kWh}$, $EF_{\text{solar}} = 30\text{ g/kWh}$).
    *   $F_{mn}(t) = \max(0, P_{mn}(t))$ è il flusso di potenza importato dal nodo adiacente $m$ verso il nodo $n$ all'ora $t$.
    *   $\text{CI}_m(t)$ è l'intensità carbonica del nodo sorgente $m$.
    Questo sistema di equazioni lineari simultanee viene risolto per ogni ora $t$ per l'intera rete, fornendo un'impronta carbonica Scope 2 dinamica ed estremamente accurata per il micro-siting.

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
*   **Strategia di Mitigazione (Approccio Gerarchico ed Algoritmi di Raccordo)**:
    Per connettere i dati nazionali di Ember con la griglia nodale di PyPSA-Eur e OSM, si applicano due livelli di raccordo:
    1.  *Mappatura Spaziale Diretta via Codici Nazionali (Approccio Baseline)*: Ciascun nodo $n$ viene mappato geograficamente al rispettivo codice paese (NUTS0). Al nodo viene assegnata l'intensità di carbonio oraria media nazionale di Ember:
        $$\text{Intensity}_{\text{grid}}(n, t) = \text{Intensity}_{\text{Ember}}(\text{Country}(n), t)$$
    2.  *Carbon Flow Tracking (Approccio Fisico Avanzato)*: Calibrazione dei singoli generatori locali di PyPSA-Eur con i mix di Ember ed esecuzione di un algoritmo di tracciamento basato sulle leggi dei flussi di rete di Kirchhoff per stimare la reale impronta di carbonio al consumo (inclusiva delle importazioni dai nodi vicini):
        $$\text{CI}_n(t) = \frac{\sum_{g \in \text{Gen}} G_{g,n}(t) \cdot EF_g + \sum_{m \in \text{Vicini}} F_{mn}(t) \cdot \text{CI}_m(t)}{\sum_{g \in \text{Gen}} G_{g,n}(t) + \sum_{m \in \text{Vicini}} F_{mn}(t)}$$
        Dove $G_{g,n}$ è la generazione locale al nodo $n$, $EF_g$ è il fattore di emissione tecnologico e $F_{mn}$ è il flusso di importazione dal nodo vicino $m$.
    3.  *Approccio Gerarchico Multicriterio*:
        *   *Filtro 1 (Nazionale - Ember)*: Escludere nazioni con normative energetiche non idonee o prezzi medi fuori budget.
        *   *Filtro 2 (Nodale - PyPSA/OSM)*: Effettuare la simulazione dinamica sui soli nodi di trasmissione superstiti per verificare la capacità termica (e calcolare l'intensità carbonica con il metodo del Carbon Flow Tracking sopra definito).
        *   *Filtro 3 (Micro-Siting - AlphaEarth)*: Solo per i top 5 nodi consigliati, analizzare un buffer geospaziale di $1\text{ km} \times 1\text{ km}$ a risoluzione di $10\text{ m}$ per ottimizzare il posizionamento esatto dei pannelli solari ed evitare zone a rischio idrogeologico.

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

---

## 7. Vincoli di Compliance e Limiti Normativi dell'Unione Europea

L'integrazione delle Direttive Europee (in particolare la Direttiva Efficienza Energetica recast EED 2023/1791, i Regolamenti Delegati 2024/1364 e bozza 2026, e la Tassonomia UE per la Finanza Sostenibile) introduce vincoli normativi rigidi che condizionano direttamente le variabili e le scelte del nostro modello di siting.

### A. Soglia di Obbligo di Reporting (EED Threshold)
*   **Variabile Condizionata**: Potenza computazionale nominale inserita dall'utente ($P_{\text{DC}}$ in $\text{MW}$).
*   **Regola di Compliance**: La direttiva EED impone l'obbligo di rendicontazione dei dati ambientali al database europeo per tutti i data center con potenza IT $\ge 500\text{ kW}$ ($0.5\text{ MW}$).
*   **Vincolo nel Modello**:
    $$\text{Status}_{\text{Reporting}}(P_{\text{DC}}) = \begin{cases} \text{MANDATORY} & \text{se } P_{\text{DC}} \ge 0.5 \text{ MW} \\ \text{VOLUNTARY} & \text{se } P_{\text{DC}} < 0.5 \text{ MW} \end{cases}$$
    I data center in regime *Mandatory* ricevono un indicatore di complessità burocratica e l'obbligo di tracciare PUE, WUE, ERF e REF per l'ottenimento dell'**Etichetta di Sostenibilità Europea**.

### B. Classificazione Dimensionale Ufficiale UE
*   **Variabile Condizionata**: $P_{\text{DC}}$ (IT load in $\text{MW}$).
*   **Regola di Compliance (Allegato IV del Regolamento Delegato)**: I data center vengono categorizzati in 5 classi dimensionali che determinano i cluster di benchmarking dell'etichetta europea:
    *   **Molto Piccolo (Very Small)**: $0.1 \text{ MW} \le P_{\text{DC}} < 0.5 \text{ MW}$
    *   **Piccolo (Small)**: $0.5 \text{ MW} \le P_{\text{DC}} < 1.0 \text{ MW}$
    *   **Medio (Medium)**: $1.0 \text{ MW} \le P_{\text{DC}} < 2.0 \text{ MW}$
    *   **Grande (Large)**: $2.0 \text{ MW} \le P_{\text{DC}} < 10.0 \text{ MW}$
    *   **Molto Grande (Very Large)**: $P_{\text{DC}} \ge 10.0 \text{ MW}$

### C. Limite Limite PUE (EU Taxonomy & Leggi Nazionali EnEfG)
*   **Variabile Condizionata**: Power Usage Effectiveness previsto del sito ($\text{PUE}_{\text{pred}}$).
*   **Regola di Compliance**: Per accedere alla finanza sostenibile (allineamento *EU Taxonomy*) e per rispettare le leggi nazionali degli Stati membri che implementano la direttiva (es. la legge tedesca EnEfG per impianti operativi post 1 Luglio 2026), il PUE deve rispettare un limite massimo stringente.
*   **Vincolo nel Modello**:
    $$\text{PUE}_{\text{pred}} \le 1.30 \quad (\text{Target Assoluto per nuovi DC})$$
    *   Se $\text{PUE}_{\text{pred}} \le 1.30 \rightarrow$ **TAXONOMY ALIGNED** (Status Verde, sblocca sconti sul debito dal 0.5% al 1.5%).
    *   Se $\text{PUE}_{\text{pred}} > 1.30 \rightarrow$ **COMPLIANCE RISK** (Status Rosso, esclude o penalizza gravemente il sito in mercati regolamentati come la Germania).
    *Il PUE orario viene stimato correlando gli embeddings climatici di AlphaEarth (temperatura di bulbo umido locale) con il fabbisogno energetico dei sistemi di raffreddamento.*

### D. Obbligo di Recupero Calore (Waste Heat Readiness & ERF)
*   **Variabile Condizionata**: Energy Reuse Factor ($\text{ERF} = E_{\text{REUSE}} / E_{\text{DC}}$).
*   **Regola di Compliance**: Tutti i nuovi data center sopra $1\text{ MW}$ devono essere predisposti per il riutilizzo del calore di scarto (*waste heat reuse ready*), e le normative locali impongono quote minime di riutilizzo effettivo (es. $\text{ERF} \ge 10\text{-}20\%$).
*   **Vincolo nel Modello**:
    Il modello di siting esegue una query spaziale tramite OSM per verificare la presenza di reti di teleriscaldamento esistenti o pianificate, o consumatori industriali/agricoli di calore entro un raggio di $2\text{ km}$ dal nodo.
    $$\text{Potenziale}_{\text{ERF}}(n) = \begin{cases} \ge 20\% & \text{se presente teleriscaldamento } \le 2\text{ km} \\ 0\% & \text{se isolato} \end{cases}$$
    Se $P_{\text{DC}} \ge 1\text{ MW}$ e $\text{Potenziale}_{\text{ERF}}(n) = 0\%$, il sito riceve una **penalizzazione del 30%** sul punteggio di compliance e un avviso di rischio di autorizzazione.

### E. Limite di Efficienza Idrica (WUE Target)
*   **Variabile Condizionata**: Water Usage Effectiveness ($\text{WUE}$ in $\text{m}^3/\text{MWh}$ o $\text{L/kWh}$).
*   **Regola di Compliance (Climate Neutral Data Centre Pact)**: Allineamento con l'accordo di neutralità climatica supportato dalla Commissione Europea.
*   **Vincolo nel Modello**:
    $$\text{WUE} \le 0.4 \quad (\text{equivalente a } 0.4 \text{ litri per kWh consumato dall'IT})$$
    Se il sistema di condizionamento previsto per il sito richiede raffreddamento evaporativo (es. torri evaporative per climi caldi) e la risorsa idrica locale (mappata tramite indici di stress idrico in AlphaEarth) è scarsa, il WUE orario calcolato supererà $0.4$, attivando un alert di **"Water Stress Vulnerability"**.

