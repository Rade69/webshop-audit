# PROMPT — Stabilizacija 5: Config cleanup

Radiš na projektu **WebshopAudit**.

Prije rada obavezno pročitaj:
- `AGENTS_webshop_audit.md`
- `CLAUDE_webshop_audit.md`

Ovo nije nova velika refaktor faza.  
Ovo je **stabilizacioni zadatak #5: config cleanup**.

Ne radi GUI redesign.  
Ne radi nove featuree.  
Ne mijenjaj scoring, shortlist, report ili category semantiku osim ako je minimalno nužno da se postojeći pragovi i default vrijednosti centralizuju i učine jasnijim.

---

# 1. Cilj zadatka

Cilj je da se **default vrijednosti, pragovi, limiti i tunable heuristike** svedu na jasno i predvidljivo mjesto, umjesto da budu rasute kroz više modula.

Do sada je mnogo toga stabilizovano:
- data contract
- shortlist/review logika
- GUI adapter sloj
- report i summary
- shared orchestration
- category inference
- sample bucket tuning
- end-to-end testovi

Sada želimo da projekat bude lakši za dalje održavanje tako što će:
- važni pragovi biti pregledni
- magic numbers biti smanjeni
- CLI i GUI defaulti biti jasniji
- tuning biti moguć bez kopanja po više fajlova

Na kraju rada treba da važi:

- ključni tunable parametri su centralizovani ili bar jasno grupisani
- nema skrivenih magic numbers za važne odluke
- config/default ponašanje je lakše pratiti
- postojeća semantika ostaje ista osim ako je eksplicitno dokumentovano zašto je mala promjena nužna

---

# 2. Najvažnije pravilo

**Ne pretvaraj config cleanup u novu refaktor fazu svega.**

Cilj nije:
- praviti novu “enterprise config” arhitekturu
- prepakovati svaki literal u posebnu klasu bez potrebe
- uvoditi apstrakciju radi apstrakcije

Cilj je:
- učiniti važne pragove i defaulte preglednim
- smanjiti rizik slučajnog drift-a
- olakšati budući tuning

---

# 3. Scope — šta tačno radiš

## 3.1. Prvo napravi inventar važnih pragova i defaulta

Obavezno pregledaj najmanje ove fajlove:

- `config.py`
- `audit/scorer.py`
- `audit/shortlist.py`
- `audit/pipeline.py`
- `audit/fetcher.py`
- `main.py`
- `gui/controllers/audit_run_controller.py`

Po potrebi pregledaj i:
- helper module koji sadrže heuristike
- report generator ako sadrži pragove
- adaptere ako imaju display threshold logiku

Treba da identifikuješ:
- score pragove
- shortlist limite
- sample bucket limite
- category inference ignore liste / fallback konfiguraciju
- fetch timeout/retry/worker/delay defaulte
- CLI default argumente
- GUI default vrijednosti koje utiču na run

---

## 3.2. Razdvoji šta je stvarni config, a šta je interna logika

Ne mora svaki literal ići u `config.py`.

Potrebno je razdvojiti:

### A — stvarni tunable config
Primjeri:
- timeout
- retries
- worker count
- delay
- max URLs
- sample bucket limiti
- score pragovi ako su namijenjeni tuningu
- shortlist limiti
- output defaulti

### B — interna logika / statičke konstante
Primjeri:
- male tehničke pomoćne vrijednosti
- jasno lokalne konstante koje nemaju smisla kao javni config
- regex helper detalji koji ne trebaju biti korisnički tunable

Cilj je:
- centralizovati ono što se stvarno može podešavati
- ne pretrpati config trivijalnim detaljima

---

## 3.3. Uskladi CLI i GUI defaulte

Pregledaj:
- šta CLI koristi kao default
- šta GUI koristi kao default
- šta shared pipeline očekuje

Ako postoje razlike, utvrdi:
- da li su namjerne
- da li su slučajan drift
- da li ih treba uskladiti

Cilj je da:
- zajednički defaulti budu jasni
- override bude moguć
- ne postoje dva različita “normalna” ponašanja bez razloga

---

## 3.4. Izvuci važne sample/shortlist pragove na jasno mjesto

Pošto su sample bucket i shortlist logika već stabilizovani, sad ih treba učiniti preglednim.

Posebno provjeri:
- `SAMPLE_MAX_ABSOLUTE`
- `SAMPLE_MAX_RATIO_OF_ISSUES`
- `SAMPLE_DISABLE_ABOVE_ISSUES`
- eventualne shortlist top N ili severity limite

Ako su već kao konstante u modulu i to je dovoljno jasno, nije nužno sve gurati u `config.py`.  
Ali mora biti jasno i lako pronađivo.

---

## 3.5. Očisti fetch/run pragove

Pregledaj:
- timeout
- retries
- delay
- concurrency / max workers
- checkpoint/resume related defaulte
- max_urls i slične run limite

Cilj je da:
- nema skrivenih različitih vrijednosti na više mjesta
- pipeline i entry pointovi čitaju iste defaulte ili jasno override-uju

---

## 3.6. Ne polomi category i scoring logiku

Ako category inference ili scoring koriste liste/konstante, procijeni da li:
- treba ostati lokalno uz logiku
- ili dio treba biti centralizovan kao konfiguracija

Nemoj nasilno izvlačiti sve u config ako to slabi čitljivost.

Pravilo:
- ono što se vjerovatno tunira → kandiduj za config
- ono što je čvrsto dio heurističke logike → može ostati blizu logike

---

## 3.7. Dodaj testove za config/default ponašanje

Dodaj ili ažuriraj testove koji štite:
- shared default vrijednosti
- CLI i GUI da ne divergiraju bez razloga
- sample/shortlist pragove da ostanu čitljivi i upotrebljivi
- fetch/run defaulte da ostanu stabilni
- config override ponašanje gdje postoji

---

# 4. Među-zavisnosti koje moraš obavezno provjeriti

Ako radiš config cleanup, moraš provjeriti uticaj na:

1. **CLI run**
   - argument defaults
   - shared pipeline config
   - očekivano ponašanje bez eksplicitnih override-a

2. **GUI run**
   - default vrijednosti u run controlleru
   - da ne ode drugim putem od CLI-a

3. **Pipeline**
   - da shared orchestration i dalje radi sa istim podrazumijevanim ponašanjem

4. **Shortlist/sample**
   - da tuning pragovi ostanu isti po semantici

5. **Fetch layer**
   - timeout, retries, delay, workers

6. **Testove**
   - da config cleanup ne uvede tihi drift

---

# 5. Šta je dozvoljeno, a šta nije

## Dozvoljeno
- centralizacija važnih defaulta i pragova
- preimenovanje / grupisanje config konstanti radi jasnoće
- male izmjene u entry pointovima da koriste shared config
- testovi za config/default ponašanje
- ostavljanje dijela konstanti lokalno ako je to razumnije

## Nije dozvoljeno
- veliki rewrite config sistema
- uvoditi nepotrebne klase/objekte/config slojeve bez stvarne koristi
- mijenjati poslovnu semantiku samo zato što je config “ljepši”
- širiti task na dokumentaciju ili GUI
- skrivati logiku u config-u tako da postane manje čitljiva

---

# 6. Kriterij uspjeha

Zadatak je završen tek kad su ispunjeni svi uslovi:

- važni tunable pragovi i defaulti su lakše pronađivi
- CLI i GUI defaulti su jasniji i usklađeniji
- nema očiglednih magic numbers za važne odluke
- sample/shortlist/fetch defaulti su pregledni
- testovi štite osnovno config/default ponašanje
- projekat je lakši za budući tuning bez velikog kopanja po kodu

---

# 7. Testovi

Dodaj ili ažuriraj testove tako da štite:

- config/default vrijednosti za shared run
- CLI i GUI da koriste iste ili jasno opravdano različite defaulte
- sample bucket pragove
- fetch timeout/retry/delay/workers defaulte
- override ponašanje gdje postoji

Ako nema potrebe za mnogo novih testova:
- radije dodaj nekoliko jakih testova nego mnogo sitnih

---

# 8. Očekivani izlaz od tebe

Vrati odgovor u ovom formatu:

## 1. Šta je bilo problematično u config/default sloju
- kratko i iskreno

## 2. Šta je sada promijenjeno
- kratko i jasno

## 3. Pogođeni fajlovi
- kompletan spisak

## 4. Koji pragovi/defaulti su sada centralizovani ili očišćeni
- sample/shortlist
- fetch/run
- CLI/GUI defaulti
- ostalo važno

## 5. Među-zavisnosti provjerene
- CLI run
- GUI run
- pipeline
- shortlist/sample
- fetch layer
- testovi

## 6. Rizici koji ostaju
- napiši iskreno šta još nije idealno
- posebno šta ostaje za završnu dokumentaciju

## 7. Testovi
- koje si pokrenuo
- koji su prošli
- šta treba ručno provjeriti

Ako je nešto blokirano, napiši:

**BLOKIRANO**
- razlog
- šta tačno treba razjasniti

---

# 9. Završna napomena

Ovaj zadatak nije “napravi ljepši config”.

Ovo je:
- uklanjanje skrivenog drift-a
- priprema za sigurniji budući tuning
- smanjenje šanse da se stabilizovani sistem kasnije pokvari sitnim, nepovezanim izmjenama
