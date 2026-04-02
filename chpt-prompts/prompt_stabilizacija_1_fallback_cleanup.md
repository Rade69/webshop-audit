# PROMPT — Stabilizacija 1: Fallback cleanup

Radiš na projektu **WebshopAudit**.

Prije rada obavezno pročitaj:
- `AGENTS_webshop_audit.md`
- `CLAUDE_webshop_audit.md`

Ovo nije nova refaktor faza iz osnovnog plana.  
Ovo je **stabilizacioni zadatak #1: fallback cleanup**.

Ne radi category inference.  
Ne radi sample bucket tuning.  
Ne radi test strategy overhaul.  
Ne radi config cleanup.  
Ne radi GUI redesign.

---

# 1. Cilj zadatka

Cilj je ukloniti ili svesti na minimum **privremene fallback mehanizme** koji su ostali poslije refaktora, a koji mogu održavati paralelnu staru logiku.

Posebno želimo izbjeći stanje:
- novi adapter / novi put postoji
- ali stari put i dalje živi paralelno
- fallback prikriva probleme umjesto da ih učini vidljivim

Na kraju rada treba biti jasno:
- koji fallbackovi su postojali
- koji su uklonjeni
- koji su zadržani
- zašto su zadržani
- zašto ne predstavljaju drugi skriveni izvor istine

---

# 2. Najvažnije pravilo

**Fallback ne smije biti trajna paralelna arhitektura.**

Fallback je dozvoljen samo ako:
- pokriva usko definisan inicijalizacioni ili edge-case scenario
- ne sadrži alternativnu business / domain semantiku
- ne održava stari put kao punu rezervnu implementaciju

Ako fallback drži staru logiku živom bez jake potrebe, treba ga ukloniti.

---

# 3. Scope — šta tačno radiš

## 3.1. Pregledaj fallback tačke

Obavezno pregledaj najmanje ove fajlove:

- `gui/tabs/results_tab.py`
- `gui/tabs/review_queue_tab.py`
- `gui/adapters/results_adapter.py`
- `gui/adapters/review_adapter.py`
- `gui/controllers/results_controller.py`
- `gui/controllers/review_controller.py`

Po potrebi pregledaj i:
- relevantne state/viewmodel fajlove
- helper/adaptor sloj
- mjesta gdje se adapter postavlja / injektuje

Treba da identifikuješ:
- gdje postoji `if adapter is None`
- gdje postoji “stari put” ako adapter nije postavljen
- gdje fallback koristi direktan rad sa sirovim redovima / kolonama
- da li fallback pokriva samo inicijalizaciju ili i glavni runtime

---

## 3.2. Klasifikuj fallbackove

Za svaki fallback odredi:

### A — legitimni fallback
Primjeri:
- kratki guard prije nego što se podaci učitaju
- prazno stanje taba
- bezopasan placeholder prikaz

### B — sumnjivi fallback
Primjeri:
- puna stara logika za mapiranje severity/reasons
- direktna interpretacija DataFrame-a ako adapter nije tu
- drugi put za formatiranje detalja i flagova
- paralelni mapping koji može divergirti od adaptera

Cilj je:
- **B** fallbackove ukloniti ili svesti na minimum
- **A** fallbackove zadržati samo ako su stvarno korisni

---

## 3.3. Očisti results tok

Posebno provjeri:
- da li `results_tab.py` i dalje ima fallback koji radi punu staru interpretaciju
- da li se detalji, badge-ovi, boje i flagovi mogu prikazati bez paralelnog puta
- da li tab može jasno failati / prikazati prazno stanje umjesto da nastavlja starim putem

Ako fallback postoji samo zato da “nikad ne pukne”, to nije dovoljan razlog ako krije problem u adapter setup-u.

---

## 3.4. Očisti review tok

Posebno provjeri:
- da li `review_queue_tab.py` i dalje može raditi kroz staru logiku ako adapter nije postavljen
- da li severity/reason prikaz ima dupli path
- da li status / detail panel koristi adapter kao glavni i jedini smisleni izvor prikazne semantike

---

## 3.5. Zadrži samo uske zaštitne mehanizme

Ako neki fallback ostaje, on smije raditi samo nešto poput:
- prikaži prazne vrijednosti
- prikaži “nema podataka”
- ne renderuj detalje dok adapter nije spreman

Ali ne smije:
- donositi business zaključke
- mapirati reason/severity/flag semantiku drugim putem
- računati vlastite display vrijednosti iz sirovih kolona ako adapter već postoji

---

## 3.6. Dodaj eksplicitnije greške gdje treba

Ako uklanjanje fallbacka znači da će se sada ranije vidjeti problem (npr. adapter nije postavljen na vrijeme), to je prihvatljivo **ako**:
- greška bude jasna
- ili stanje bude jasno prazno / disabled
- i ne razbija bez potrebe normalan tok rada

Bolje je:
- jasan, kontrolisan problem

nego:
- tihi paralelni stari put

---

# 4. Među-zavisnosti koje moraš obavezno provjeriti

Ako čistiš fallbackove, moraš provjeriti uticaj na:

1. **Results tab**
   - učitavanje rezultata
   - prikaz tabele
   - selection/details
   - badge/status prikaz

2. **Review queue tab**
   - učitavanje queue-a
   - severity/reason prikaz
   - detail panel
   - status/note workflow

3. **Adapter setup**
   - da se adapter uvijek postavlja na vrijeme u glavnom toku
   - da tab ne ostane bez podataka u legitimnom run-u

4. **Controller tok**
   - da controller i dalje predaje dovoljno podataka za adapter setup

5. **GUI smoke ponašanje**
   - glavni tok mora ostati funkcionalan

---

# 5. Šta je dozvoljeno, a šta nije

## Dozvoljeno
- uklanjanje fallback grana koje održavaju staru logiku
- svođenje fallbacka na prazan / neutralan prikaz
- manje izmjene u controllerima ako su potrebne da adapter uvijek bude spreman
- dodavanje guardova sa jasnim ponašanjem
- testovi za adapter setup i GUI ponašanje

## Nije dozvoljeno
- novi adapter redesign
- GUI feature razvoj
- category inference izmjene
- shortlist/scoring/report semantika izmjene
- velika arhitektonska promjena izvan cleanup scope-a

---

# 6. Kriterij uspjeha

Zadatak je završen tek kad su ispunjeni svi uslovi:

- nema paralelnog starog puta za glavne display semantike
- fallbackovi, ako postoje, svedeni su na uske i bezopasne slučajeve
- adapter ostaje glavni put za display interpretaciju
- results i review tok i dalje rade
- jasno je dokumentovano koji fallback je zadržan i zašto

---

# 7. Testovi

Dodaj ili ažuriraj testove tako da štite:

- adapter se postavlja u očekivanom toku
- tabovi ne koriste staru semantiku kad adapter postoji
- bez adaptera tab ide u jasan neutralan state, ne u paralelnu staru logiku
- glavni results/review tok i dalje radi

Ako nema pun GUI runtime test:
- napiši šta je pokriveno testovima
- šta je statički provjereno
- šta treba ručno klik-proći

---

# 8. Očekivani izlaz od tebe

Vrati odgovor u ovom formatu:

## 1. Koji fallbackovi su postojali
- kratak spisak
- gdje su bili
- zašto su bili problem

## 2. Šta je uklonjeno
- konkretno i kratko

## 3. Šta je zadržano
- gdje
- zašto
- zašto nije opasno

## 4. Pogođeni fajlovi
- kompletan spisak

## 5. Među-zavisnosti provjerene
- results tok
- review tok
- adapter setup
- controller tok
- testovi / ručna provjera

## 6. Rizici koji ostaju
- napiši iskreno ako još postoji nešto što liči na fallback dug

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

Ovaj zadatak nije “uljepšavanje” koda.

Ovo je uklanjanje privremenih mostova koji kasnije stvaraju:
- skriveni drift
- teško reprodukovane bugove
- lažan osjećaj stabilnosti

Ako vidiš druge probleme, navedi ih pod **Rizici koji ostaju**, ali ih ne rješavaj ovdje osim ako direktno blokiraju fallback cleanup.
