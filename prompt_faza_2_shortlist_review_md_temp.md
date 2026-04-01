# PROMPT — FAZA 2: Refaktor shortlist i review logike

Radiš na projektu **WebshopAudit**.

Prije rada obavezno pročitaj:
- `AGENTS_webshop_audit.md`
- `CLAUDE_webshop_audit.md`

Ovaj zadatak je **isključivo Faza 2** iz plana refaktora.  
Podrazumijeva se da je **Faza 1 završena** i da je data contract kroz sistem već konsolidovan.

Ne radi Fazu 3, 4 ili 5.  
Ne radi GUI polish.  
Ne radi opšti redesign rezultata.  
Ne uvodi nove featuree van scope-a shortlist/review logike.

---

# 1. Cilj zadatka

Cilj je da se postojeća shortlist i review logika pretvori iz preširokog, bučnog mehanizma u **stvarno koristan sistem za ljudsku reviziju**.

Trenutni problem koji treba riješiti:

- shortlist lako postane skoro cijeli uzorak
- review queue gubi smisao kad je zatrpan
- nisu jasno odvojeni:
  - kritični problemi
  - sumnjivi problemi
  - samo nizak score
  - ne-produktne stranice
- korisnik ne dobija dovoljno jasno objašnjenje **zašto** je URL završio u reviziji

Na kraju rada shortlist mora biti:
- manji
- smisleniji
- objašnjiv
- stabilan
- odvojen od samog GUI workflow-a za ručnu obradu

---

# 2. Najvažnije pravilo

**Shortlist i review queue nisu ista stvar.**

- `audit/shortlist.py` određuje koji kandidati ulaze u reviziju
- GUI koristi tu listu, prikazuje je i upravlja statusima / bilješkama / ručnim označavanjem
- GUI ne smije postati drugi engine za shortlist odluke

Drugim riječima:

**pravila za ulazak u shortlist pripadaju domain sloju, ne tabovima i ne kontrolerima.**

---

# 3. Scope — šta tačno radiš

## 3.1. Prvo analiziraj postojeći shortlist tok

Obavezno pregledaj:
- `audit/shortlist.py`
- `audit/scorer.py`
- `audit/exporters.py`
- `audit/pipeline.py`
- `gui/controllers/review_controller.py`
- `gui/tabs/review_queue_tab.py`

Po potrebi pregledaj i:
- `results_controller.py`
- viewmodel/state za review red
- output CSV fajlove ako postoje

Treba da potvrdiš:
- kako se trenutno formira `manual_review_candidates.csv`
- da li se lista puni po `top_n`
- da li su problematični URL-ovi pomiješani sa samo najnižim scoreovima
- da li postoji reason/flag logika ili je preslaba

---

## 3.2. Uvedi severity model

Shortlist treba da razlikuje barem ove nivoe:

### Kritično
Primjeri:
- fetch error
- non-200
- stranica vjerovatno nije produktna
- ključni structured data ili price signali ozbiljno nedostaju uz dovoljno jak signal da je stranica produktna

### Potrebna provjera
Primjeri:
- canonical mismatch
- noindex
- schema/HTML neslaganje
- sumnjivo nizak content ili nedovoljno signala

### Nizak prioritet / informativno
Primjeri:
- samo niži overall score bez jasnog kritičnog razloga
- rubni slučajevi koji nisu odmah alarm

Nemoj ovo raditi samo kozmetički.  
Severity mora biti dio domain logike i mora uticati na shortlist odluku.

---

## 3.3. Uvedi reason code-ove

Svaki shortlist kandidat mora imati jasan razlog ili više razloga.

Primjeri reason code-ova mogu biti u ovom stilu:
- `fetch-error`
- `non-200`
- `not-product-page`
- `missing-price`
- `missing-schema-product`
- `canonical-mismatch`
- `noindex`
- `low-content`
- `js-rendered-risk`

Ne moraš slijepo koristiti ove tačne stringove, ali:
- reason code mora biti stabilan
- mora biti mašinski čitljiv
- mora biti upotrebljiv u GUI prikazu i eksportu
- mora jasno objašnjavati shortlist ulazak

Ako jedan kandidat ima više razloga, to treba biti podržano.

---

## 3.4. Redizajniraj kriterij za ulazak u shortlist

Potrebno je da shortlist ne bude više:
- “najgorih N bez obzira na razlog”

nego:
- prioritetna lista po severity + signalima + eventualno score kontekstu

Očekujem da razdvojiš barem:
1. automatski uključene kritične slučajeve
2. sumnjive slučajeve za provjeru
3. eventualni ograničeni broj dodatnih slabijih kandidata radi uzorka

Ako koristiš `top_n`, ono smije biti samo pomoćni limit, ne glavni princip.

---

## 3.5. Očisti odnos između shortlist i review queue sloja

Potrebno je jasno razdvojiti:

### Domain sloj
- shortlist ulazak
- severity
- reason code
- osnovni export kandidata

### GUI sloj
- status pregleda
- ručno označavanje
- bilješke
- filtriranje i pregled kandidata

GUI ne smije ponovo odlučivati da li je nešto shortlist kandidat osim za ručno dodavanje/uklanjanje gdje to workflow traži.

---

## 3.6. Ažuriraj eksport i GUI prikaz gdje je potrebno

Ako uvedeš severity i reason code, provjeri uticaj na:
- `manual_review_candidates.csv`
- review queue prikaz
- kolonu “Razlog”
- kolonu “Oznake”
- eventualne statuse ili detalje na desnom panelu

Ako GUI treba prikazati severity i razloge, uradi to **minimalno i čisto**, bez širenja scope-a na potpuni GUI redesign.

---

## 3.7. Dodaj testove

Dodaj ili ažuriraj testove tako da štite:

- da kritični URL-ovi sigurno ulaze u shortlist
- da niski score sam po sebi ne zatrpava shortlist
- da reason code postoji i ima smisla
- da severity postoji i ima smisla
- da se ne-produktne stranice tretiraju konzistentno
- da review export i GUI zavisnosti ne pucaju zbog novog modela

Testovi treba da štite ponašanje, ne samo internu implementaciju.

---

# 4. Među-zavisnosti koje moraš obavezno provjeriti

Ako mijenjaš shortlist model, moraš provjeriti uticaj na:

1. **`manual_review_candidates.csv`**
   - shape
   - reason/severity kolone
   - broj kandidata
   - smislenost liste

2. **`best_products_sample.csv`**
   - da nije slučajno pogođen
   - da ostane semantički jasan

3. **Review controller**
   - da i dalje može učitati red za reviziju
   - da koristi nove reason/severity podatke gdje je potrebno

4. **Review queue tab**
   - tabela
   - detalji desnog panela
   - oznake / razlog / status prikaz

5. **Results tab**
   - ako prikazuje review oznake ili shortlist status, provjeri da nije slomljen

6. **Pipeline**
   - da shortlist/export i dalje rade kroz glavni tok bez posebnih hackova

---

# 5. Šta je dozvoljeno, a šta nije

## Dozvoljeno
- refaktor `audit/shortlist.py`
- manje dopune u `scorer.py` ako su potrebne za severity/reason signal
- male izmjene u exporterima i review controlleru da podrže novi model
- male GUI izmjene za prikaz severity/reason podataka
- testovi za novo ponašanje

## Nije dozvoljeno
- potpuni GUI redesign
- refaktor cijelog results taba izvan onoga što je nužno
- mijenjanje canonical data contracta iz Faze 1 bez jakog razloga
- veći report redesign
- orchestration refaktor
- dodavanje novih “smart AI” heuristika van shortlist scope-a

---

# 6. Kriterij uspjeha

Zadatak je završen tek kad su ispunjeni svi uslovi:

- shortlist više ne zatrpava review queue bez razloga
- postoje severity nivoi
- postoje reason code-ovi
- kritični slučajevi ulaze prioritetno
- samo nizak score nije dovoljan da napuni shortlist
- GUI review workflow i dalje radi
- eksport kandidata je jasan i upotrebljiv
- testovi štite novo ponašanje

---

# 7. Očekivani izlaz od tebe

Vrati odgovor u ovom formatu:

## 1. Šta je promijenjeno
- kratko i jasno

## 2. Pogođeni fajlovi
- kompletan spisak

## 3. Novi shortlist model
- kako radi severity
- kako rade reason code-ovi
- po kojem principu kandidati ulaze

## 4. Među-zavisnosti provjerene
- `manual_review_candidates.csv`
- `best_products_sample.csv`
- review controller
- review queue tab
- results tab
- pipeline
- testovi

## 5. Rizici koji ostaju
- napiši iskreno ako nešto još nije idealno

## 6. Testovi
- koje si pokrenuo
- koji su prošli
- šta ostaje za ručnu provjeru

Ako je nešto blokirano, napiši:

**BLOKIRANO**
- razlog
- fajlovi / slojevi koje blokira
- šta tačno treba razjasniti

---

# 8. Završna napomena

Ne pokušavaj u ovom zadatku sređivati:
- GUI arhitekturu u širinu
- category inference
- report generator osim minimalno ako baš zavisi od shortlist shape-a
- CLI/GUI orchestration

Ovaj zadatak je uspješan samo ako disciplinovano zatvoriš **Fazu 2 — shortlist i review logiku**.

Ako vidiš druge probleme, navedi ih pod **Rizici koji ostaju**, ali ih ne rješavaj osim ako direktno blokiraju Fazu 2.

