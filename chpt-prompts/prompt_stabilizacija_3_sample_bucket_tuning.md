# PROMPT — Stabilizacija 3: Sample bucket tuning

Radiš na projektu **WebshopAudit**.

Prije rada obavezno pročitaj:
- `AGENTS_webshop_audit.md`
- `CLAUDE_webshop_audit.md`

Ovo nije nova velika refaktor faza.  
Ovo je **stabilizacioni zadatak #3: sample bucket tuning**.

Ne diraj category inference osim ako je minimalno nužno zbog sample logike.  
Ne radi end-to-end test strategy overhaul.  
Ne radi config cleanup.  
Ne radi GUI redesign.  
Ne mijenjaj scoring ili severity semantiku za stvarne problematične kandidate.

---

# 1. Cilj zadatka

Cilj je da **sample bucket prestane biti bučan**, a da i dalje zadrži svoju korisnu funkciju.

Trenutno shortlist više nije neobjašnjiv, ali sample kandidati tipa:
- `Sample (Good Score)`

mogu i dalje:
- zauzimati previše mjesta u shortlisti
- smanjivati signal-to-noise
- stvarati dojam da previše stranica traži ručni pregled iako zapravo nemaju problem

Na kraju rada treba da važi:

- stvarni problematični kandidati imaju prioritet
- sample kandidati su ograničeni i kontrolisani
- shortlist ostaje pregledan i objašnjiv
- sample bucket postoji samo kao dodatak, ne kao dominantan dio review reda

---

# 2. Najvažnije pravilo

**Sample bucket ne smije preuzeti shortlist.**

Shortlist prvenstveno služi za:
- stvarne probleme
- sumnjive slučajeve
- stranice koje stvarno traže pažnju

Sample bucket služi samo za:
- mali broj reprezentativnih “dobrih” ili neutralnih kandidata radi poređenja / benchmarka

Ako sample bucket počne puniti polovinu liste bez jasne potrebe, to je loš rezultat.

---

# 3. Scope — šta tačno radiš

## 3.1. Pregledaj postojeću sample logiku

Obavezno pregledaj:
- `audit/shortlist.py`
- po potrebi `audit/scorer.py`
- `audit/exporters.py`
- `audit/pipeline.py`

Po potrebi pregledaj i:
- `manual_review_candidates.csv`
- report shortlist prilog
- testove za shortlist

Treba da potvrdiš:
- kada kandidat dobija sample reason code
- koliko sample kandidata može ući
- da li je limit globalan ili implicitno neograničen
- da li sample bucket zavisi od broja stvarnih problema
- kako sample kandidati utiču na ukupan broj review kandidata

---

## 3.2. Uvedi kontrolisan limit za sample bucket

Potrebno je da sample kandidati budu ograničeni.

Rješenje može biti jedno od ovih ili slično ako nađeš bolje:

### Opcija A — fiksni limit
npr. maksimalno 2 ili 3 sample kandidata po run-u

### Opcija B — relativni limit
npr. sample kandidati ne smiju biti više od određenog procenta stvarnih problematičnih kandidata

### Opcija C — hibrid
npr.:
- maksimalno 3 sample kandidata
- i nikad više od 30–40% shortlist kandidata

Ne moraš slijepo koristiti ove brojeve, ali mora postojati:
- jasan limit
- jasan razlog
- kontrolisano ponašanje

---

## 3.3. Daj prioritet stvarnim problemima

Ako ima dovoljno:
- CRITICAL
- HIGH
- MEDIUM

kandidata, sample bucket treba biti:
- manji
- ili potpuno isključen ako nema smisla

Drugim riječima:

**sample bucket treba zavisiti od realnog problema u datasetu, ne samo od toga da “ima mjesta”.**

---

## 3.4. Održi sample bucket korisnim

Nemoj ga samo brutalno ugasiti.

Sample bucket i dalje može biti koristan za:
- poređenje dobrih i loših stranica
- benchmark
- ručni sanity check

Ali mora biti:
- mali
- jasno označen
- dosljedan

Ako ostaje sample reason code:
- neka ostane jasan (`sample-good-score` ili slično)
- neka ne bude pomiješan sa stvarnim problem reason kodovima

---

## 3.5. Ne diraj stvarne shortlist razloge

Ovaj zadatak nije za:
- promjenu CRITICAL/HIGH/MEDIUM logike
- promjenu canonical mismatch prioriteta
- promjenu missing price / missing schema logike

Fokus je samo na:
- **sample bucket količini i ulozi**

---

## 3.6. Uskladi report i CSV prikaz ako je potrebno

Ako sample bucket broj bude smanjen ili drugačije organizovan, provjeri:
- `manual_review_candidates.csv`
- shortlist prilog u reportu

Report treba i dalje jasno pokazivati:
- šta je stvarni problem
- šta je sample kandidat

Ali ne treba dodatni report hack ako to već dolazi iz canonical shortlist rezultata.

---

# 4. Među-zavisnosti koje moraš obavezno provjeriti

Ako tuniraš sample bucket, moraš provjeriti uticaj na:

1. **`manual_review_candidates.csv`**
   - broj kandidata
   - odnos stvarnih problema i sample kandidata
   - reason/severity konzistentnost

2. **`audit_report.docx`**
   - shortlist prilog
   - da sample kandidati ostanu jasno označeni
   - da shortlist izgleda manje bučno i smislenije

3. **Shortlist logika**
   - da stvarni problemi ostaju prioritetni
   - da sample bucket ne naruši severity model

4. **Output konzistentnost**
   - da se ne polome eksport i prikaz

5. **Testovi**
   - da nova pravila budu zaštićena

---

# 5. Šta je dozvoljeno, a šta nije

## Dozvoljeno
- tuning sample bucket limita u `audit/shortlist.py`
- manje helper funkcije za odvajanje sample i issue kandidata
- testovi za sample bucket ponašanje
- eventualno jasno dokumentovan threshold u config-u ako je to najprirodnije mjesto

## Nije dozvoljeno
- mijenjati scoring model
- mijenjati severity model za stvarne probleme
- category inference izmjene
- GUI izmjene
- report-only hackovi da shortlist “izgleda bolje”
- potpuno uklanjanje sample bucket-a bez dobrog razloga

---

# 6. Kriterij uspjeha

Zadatak je završen tek kad su ispunjeni svi uslovi:

- sample bucket više ne zatrpava shortlist
- stvarni problemi imaju jasan prioritet
- sample kandidati su i dalje prisutni, ali kontrolisano
- reason/severity logika ostaje konzistentna
- report i CSV jasno razlikuju sample od stvarnih problema
- testovi štite novo ponašanje

---

# 7. Testovi

Dodaj ili ažuriraj testove tako da štite:

- sample bucket ima limit
- sample kandidati ne mogu nadjačati stvarne probleme
- sample kandidati ostaju jasno označeni
- shortlist sa mnogo stvarnih problema sadrži manje ili nimalo sample kandidata
- shortlist sa malo stvarnih problema može imati mali broj sample kandidata
- CSV/report prikaz ostaje konzistentan

Ako nemaš full report integration test:
- napiši šta je pokriveno na shortlist nivou
- šta treba ručno provjeriti na stvarnom outputu

---

# 8. Očekivani izlaz od tebe

Vrati odgovor u ovom formatu:

## 1. Šta je bio stvarni problem sample bucketa
- kratko i iskreno

## 2. Šta je sada promijenjeno
- kratko i jasno

## 3. Pogođeni fajlovi
- kompletan spisak

## 4. Novo sample bucket pravilo
- koliki je limit
- kako zavisi od stvarnih problema
- kako ostaje koristan, ali ne bučan

## 5. Među-zavisnosti provjerene
- `manual_review_candidates.csv`
- `audit_report.docx`
- shortlist logika
- testovi

## 6. Rizici koji ostaju
- napiši iskreno ako još postoji neki rubni slučaj

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

Ovaj zadatak nije “smanji broj kandidata po svaku cijenu”.

Ovo je:
- tuning signal-to-noise odnosa
- zaštita vrijednosti review reda
- održavanje sample bucketa kao korisnog, ali sporednog mehanizma
