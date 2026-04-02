# PROMPT — Završni korak: Kratka arhitektonska dokumentacija

Radiš na projektu **WebshopAudit**.

Prije rada obavezno pročitaj:
- `AGENTS_webshop_audit.md`
- `CLAUDE_webshop_audit.md`

Ovo nije nova refaktor faza.  
Ovo je **završni stabilizacioni zadatak: kratka arhitektonska dokumentacija**.

Ne radi nove featuree.  
Ne radi GUI redesign.  
Ne radi novi refaktor osim ako je minimalno nužno da dokumentacija ne bude netačna.  
Primarni cilj je da ostane **jasan, praktičan i kratak dokument** koji pomaže budućem radu na projektu.

---

# 1. Cilj zadatka

Cilj je da napraviš **jedan kratak, praktičan `.md` dokument** koji objašnjava kako projekat sada stvarno funkcioniše nakon svih refaktora i stabilizacija.

Dokument treba da spriječi povratak haosa tako što jasno kaže:

- gdje je source-of-truth za data contract
- gdje živi shared orchestration
- šta pripada domain sloju
- šta pripada GUI sloju
- kako rade shortlist i report
- šta su poznati preostali tehnički dugovi
- šta se ne smije raditi pri budućim izmjenama

Ovo nije “lijepa produkt dokumentacija”.  
Ovo je **radna arhitektonska mapa za razvoj**.

---

# 2. Najvažnije pravilo

**Dokument mora biti praktičan, kratak i istinit.**

Ne treba:
- generičke arhitektonske fraze
- nepotrebna teorija
- marketing jezik
- duga objašnjenja koja niko neće čitati

Treba:
- stvarno stanje projekta
- jasna pravila
- konkretni moduli i odgovornosti
- konkretni poznati dugovi

Ako nešto nije savršeno, napiši to direktno.

---

# 3. Scope — šta tačno radiš

## 3.1. Napravi jedan glavni `.md` dokument

Naziv dokumenta može biti nešto poput:
- `ARCHITECTURE.md`
- `ARCHITECTURE_OVERVIEW.md`
- `WEBSHOP_AUDIT_ARCHITECTURE.md`

Izaberi ime koje je jasno i trajno.

Dokument treba biti dovoljno kratak da ga ljudi stvarno čitaju, ali dovoljno sadržajan da bude koristan.

---

## 3.2. Obavezne sekcije dokumenta

Dokument mora imati barem ove sekcije:

### A. Svrha projekta
Kratko:
- šta alat radi
- koji je glavni tok
- koji su glavni outputi

### B. Glavni tok podataka
Od:
- URL/sitemap inputa
preko:
- fetch/extract/scoring/shortlist/report
do:
- CSV/report/GUI prikaza

Ovo treba biti kratko, ali jasno.

### C. Source-of-truth moduli
Mora jasno navesti:
- gdje je data contract source-of-truth
- gdje je shared orchestration source-of-truth
- gdje živi shortlist logika
- gdje živi report logika
- gdje živi category inference
- gdje žive GUI adapteri

### D. Podjela odgovornosti po slojevima
Mora jasno razlikovati:
- domain sloj
- orchestration sloj
- GUI/controller/viewmodel/adaptor sloj
- report/export sloj

### E. Pravila za buduće izmjene
Kratka, konkretna pravila, npr:
- ne uvoditi nove alias kolone
- ne računati business logiku u tabovima
- ne raditi report-only hackove za domain probleme
- ne uvoditi paralelni CLI/GUI tok

### F. Poznati preostali tehnički dugovi
Samo realni i korisni, npr:
- category inference još nije savršen
- DOCX formatting edge case-ovi
- GUI runtime smoke test još ostaje ručna provjera
- QSettings/user override granice
- sve drugo što stvarno vrijedi zabilježiti

### G. Preporučeni redoslijed za budući razvoj
Kratko:
- šta je bezbjedno dalje razvijati
- šta prvo provjeriti prije većih izmjena
- gdje su osjetljive tačke

---

## 3.3. Dokumentuj stvarno stanje, ne idealizovano stanje

Ako fallback više ne postoji — napiši to.  
Ako category inference i dalje ima ograničenja — napiši to.  
Ako report radi, ali DOCX ima sitne formatting edge-caseove — napiši to.

Cilj je da dokument bude **koristan budućem developeru**, ne da impresionira.

---

## 3.4. Dodaj kratku “šta ne dirati napamet” sekciju

Vrlo korisno je imati kratku listu tipa:

- ne mijenjati canonical kolone bez pune propagacije
- ne unositi logiku u tabove
- ne uvoditi drugi orchestration put mimo `run_audit()`
- ne popravljati category summary u reportu ako je problem u scorer-u
- ne dodavati sample bucket logiku u GUI

Ovo treba biti kratko, ali jasno.

---

# 4. Među-zavisnosti koje moraš obavezno provjeriti

Prije nego napišeš dokument, provjeri da dokumentacija odgovara stvarnom kodu za:

1. **Data contract**
   - `audit/extractor.py`
   - `audit/scorer.py`

2. **Shared orchestration**
   - `audit/pipeline.py`
   - `main.py`
   - `gui/controllers/audit_run_controller.py`

3. **Shortlist i report**
   - `audit/shortlist.py`
   - `audit/report_generator.py`

4. **GUI adapter sloj**
   - `gui/adapters/results_adapter.py`
   - `gui/adapters/review_adapter.py`

5. **Config/default sloj**
   - `config.py`

Dokument ne smije opisivati zastarjelo stanje.

---

# 5. Šta je dozvoljeno, a šta nije

## Dozvoljeno
- napraviti jedan dobar `.md` dokument
- dodati kratak ASCII dijagram ako pomaže
- dodati kratku listu poznatih dugova
- minimalno korigovati dokument ako usput primijetiš da je neka stvar u kodu drugačija nego što se mislilo

## Nije dozvoljeno
- pretvarati ovo u veliku tehničku knjigu
- pisati generičku teorijsku arhitekturu
- raditi novi refaktor samo zato da dokument izgleda ljepše
- skrivati postojeće tehničke dugove

---

# 6. Kriterij uspjeha

Zadatak je završen tek kad su ispunjeni svi uslovi:

- postoji jedan jasan `.md` arhitektonski dokument
- dokument odgovara stvarnom stanju projekta
- dokument je kratak i praktičan
- source-of-truth moduli su jasno navedeni
- pravila za buduće izmjene su jasno navedena
- poznati tehnički dugovi su zapisani bez uljepšavanja

---

# 7. Očekivani izlaz od tebe

Vrati odgovor u ovom formatu:

## 1. Koji dokument je napravljen
- naziv fajla

## 2. Šta dokument pokriva
- kratko i jasno

## 3. Na koje module je dokument vezan
- glavni source-of-truth moduli

## 4. Koji tehnički dugovi su eksplicitno zabilježeni
- kratak spisak

## 5. Rizici koji ostaju
- napiši iskreno ako dokument ne pokriva nešto važno

Ako je nešto blokirano, napiši:

**BLOKIRANO**
- razlog
- šta tačno treba razjasniti

---

# 8. Završna napomena

Ovaj zadatak je važan jer zatvara ciklus refaktora.

Bez ovog dokumenta:
- arhitektura će se opet razvodniti
- nova logika će opet curiti u pogrešne slojeve
- sljedeći refaktor će biti skuplji nego što treba

Napravi dokument koji bi i sam želio da zatekneš za 6 mjeseci kad se vratiš na ovaj projekat.
