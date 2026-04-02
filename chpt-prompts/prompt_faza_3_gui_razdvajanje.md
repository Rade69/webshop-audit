# PROMPT — FAZA 3: Razdvajanje GUI prikaza od domain interpretacije

Radiš na projektu **WebshopAudit**.

Prije rada obavezno pročitaj:
- `AGENTS_webshop_audit.md`
- `CLAUDE_webshop_audit.md`

Ovaj zadatak je **isključivo Faza 3** iz plana refaktora.  
Podrazumijeva se da su:
- **Faza 1** (data contract konsolidacija) završena
- **Faza 2** (shortlist i review logika) završena

Ne radi Fazu 4 ili 5.  
Ne radi novi feature development.  
Ne radi vizuelni redesign aplikacije.  
Ne mijenjaj scoring, shortlist ili report logiku osim ako je nužno da se očisti GUI sloj od pogrešne odgovornosti.

---

# 1. Cilj zadatka

Cilj je da GUI sloj postane **tanji, predvidljiviji i lakši za održavanje**, tako što će se:

- smanjiti količina domain interpretacije u tabovima
- prebaciti tumačenje podataka u controller / viewmodel / state sloj
- ukloniti lokalni fallbackovi i “mali hackovi” koji skrivaju backend problem
- jasno razdvojiti:
  - prikaz
  - orchestration
  - interpretaciju audit podataka

Na kraju rada GUI mora i dalje raditi, ali sa manje logike u samim tabovima.

---

# 2. Najvažnije pravilo

**Tabovi su view sloj, ne business sloj.**

To znači:

### Tab smije:
- prikazivati podatke
- emitovati akcije / signale
- reagovati na selection change
- raditi čisto UI formatiranje i layout
- prikazivati već pripremljene badge/label/filter vrijednosti

### Tab ne smije:
- tumačiti canonical DataFrame kao da je domain engine
- uvoditi vlastite heuristike za score / flags / severity / review logiku
- izmišljati fallback vrijednosti da “ne pukne”
- imati dupliranu logiku iz controller/scorer/shortlist sloja

---

# 3. Scope — šta tačno radiš

## 3.1. Prvo identifikuj GUI fajlove koji nose previše odgovornosti

Obavezno pregledaj najmanje ove fajlove:

### Tabovi
- `gui/tabs/results_tab.py`
- `gui/tabs/review_queue_tab.py`
- `gui/tabs/input_tab.py`

### Controller sloj
- `gui/controllers/results_controller.py`
- `gui/controllers/review_controller.py`
- `gui/controllers/audit_run_controller.py`

### State / viewmodel sloj
- svi relevantni state/viewmodel fajlovi koje koriste results i review tokovi

### Domain zavisnosti koje ne smiješ slomiti
- `audit/scorer.py`
- `audit/shortlist.py`
- `audit/pipeline.py`

Potrebno je potvrditi:
- gdje tabovi direktno tumače DataFrame kolone
- gdje tabovi imaju previše filter logike
- gdje tabovi imaju badge/reason/severity interpretaciju koja zapravo pripada controlleru ili helper sloju
- gdje postoji dupliranje između controllera i taba

---

## 3.2. Premjesti interpretaciju podataka iz tabova

Potrebno je iz tabova izvući logiku koja radi stvari poput:

- tumačenje flagova
- tumačenje severity/reason vrijednosti
- pravljenje human-readable labela iz domain kolona
- odluke oko toga šta je “problem”, šta je “sample”, šta je “kritično”
- priprema data strukture za prikaz detalja

Ova logika treba završiti u jednom od sljedećih mjesta:
- controller
- viewmodel/state
- mali, jasni GUI helper/adaptor sloj

Ne prebacuj je naslijepo.  
Prvo utvrdi gdje joj je najprirodnije mjesto.

---

## 3.3. Očisti results tab

Posebno obrati pažnju na `results_tab.py`.

Cilj je da results tab:
- prikazuje već pripremljene vrijednosti
- ne računa sam značenje flagova
- ne odlučuje sam šta ide u badge, šta je warning, šta je review kandidat
- ne barata direktno sa previše DataFrame detalja ako controller može pripremiti view-friendly model

Ako postoje:
- lokalni maperi
- inline heuristike
- fallback stringovi koji skrivaju problem
- suviše logike u selection/detail prikazu

premjesti ih van taba.

---

## 3.4. Očisti review queue tab

Posebno obrati pažnju na `review_queue_tab.py`.

Cilj je da review queue tab:
- prikazuje shortlist/review podatke koje dobije
- ne rekonstruiše reason/severity logiku iz sirovih kolona
- ne tumači sam šta znače review oznake
- ne sadrži business pravila za shortlist

Ako postoji mapiranje za:
- severity label
- reason label
- sample/problem razlikovanje
- status badge

to treba biti izvan taba, osim najtanji prikazni sloj.

---

## 3.5. Očisti input / run orchestration gdje ima smisla

Ako `input_tab.py` ili `audit_run_controller.py` imaju:
- miješanje UI i orchestration logike
- direktne zavisnosti koje bi trebale biti u controlleru
- previše posla u view sloju

očisti to, ali bez širenja scope-a na kompletnu orchestration konsolidaciju iz Faze 5.

Drugim riječima:
- dozvoljeno je ukloniti očigledno miješanje odgovornosti
- nije dozvoljeno raditi puni CLI/GUI orchestration redesign

---

## 3.6. Uvedi jasan view-friendly adapter sloj ako je potreban

Ako vidiš da controlleri trenutno šalju tabovima previše sirov DataFrame logike, dozvoljeno je uvesti mali adapter/helper/viewmodel sloj koji priprema:

- display labels
- badge tekstove
- reason tekstove
- summary detail blokove
- filter opcije za prikaz

Ali:
- sloj mora biti mali i jasan
- ne smije postati novi skriveni business engine
- mora koristiti canonical podatke, ne lokalne alias hackove

---

## 3.7. Ne diraj domain logiku osim ako je nužno

Ako primijetiš da je problem u scorer/shortlist sloju, ne refaktoriši ga ovdje osim ako je apsolutno potrebno da GUI prestane raditi pogrešnu stvar.

Ako moraš nešto minimalno dodati u domain sloj:
- objasni tačno zašto
- svedi promjenu na minimum
- ne mijenjaj semantiku faza 1 i 2

---

# 4. Među-zavisnosti koje moraš obavezno provjeriti

Ako refaktorišeš GUI sloj, moraš provjeriti uticaj na:

1. **Results tab**
   - tabela rezultata
   - filteri
   - detalji selektovanog reda
   - badge / status prikaz
   - review status prikaz ako postoji

2. **Review queue tab**
   - tabela kandidata
   - prikaz severity/reason
   - desni panel / detalji
   - status i bilješke

3. **Controller sloj**
   - da tabovi i dalje dobijaju sve što im treba
   - da controlleri ne postanu God object

4. **State / viewmodel sloj**
   - da stanje ostane jasno
   - da nema duplog izvora istine

5. **Pipeline integration**
   - GUI i dalje može pokrenuti audit
   - GUI i dalje može učitati rezultate i shortlist

6. **Report / export indirektno**
   - ne smiješ pokvariti putanju samo zato što si promijenio GUI helpere

---

# 5. Šta je dozvoljeno, a šta nije

## Dozvoljeno
- izvlačenje helper funkcija iz tabova
- premještanje interpretacije u controller/viewmodel/adaptor sloj
- tanji tab API
- manje čišćenje state sloja
- dodavanje testova za controller/viewmodel ponašanje
- smanjenje duplikacije između results/review prikaza

## Nije dozvoljeno
- mijenjati canonical kolone
- mijenjati shortlist model
- mijenjati scoring model
- raditi report redesign
- raditi kompletan orchestration redesign
- raditi vizuelni redizajn aplikacije
- uvoditi masivne nove apstrakcije bez jasne potrebe

---

# 6. Kriterij uspjeha

Zadatak je završen tek kad su ispunjeni svi uslovi:

- tabovi sadrže manje domain interpretacije nego prije
- controller / viewmodel / helper sloj preuzima pripremu prikaznih podataka
- results i review prikaz i dalje rade
- GUI više ne koristi lokalne hackove da prikrije problem
- testovi ili ručne provjere potvrđuju da glavni tok nije slomljen
- kod je čitljiviji i lakši za dalje održavanje

---

# 7. Testovi

Dodaj ili ažuriraj testove tako da štite:

- controller priprema ispravan display model za tab
- review prikaz dobija reason/severity u očekivanom formatu
- results prikaz dobija badge/status podatke bez da tab sam izračunava semantiku
- glavni GUI tok i dalje radi za:
  - učitavanje rezultata
  - odabir reda
  - prikaz detalja
  - review queue prikaz

Ako GUI runtime testovi nisu potpuni u okruženju:
- jasno napiši šta si pokrio testovima
- šta si provjerio statički
- šta treba ručno klik-proći

---

# 8. Očekivani izlaz od tebe

Vrati odgovor u ovom formatu:

## 1. Šta je promijenjeno
- kratko i jasno

## 2. Pogođeni fajlovi
- kompletan spisak

## 3. Šta je izvučeno iz tabova
- koje logike više nisu u `results_tab.py`
- koje logike više nisu u `review_queue_tab.py`
- šta sada radi controller / viewmodel / helper sloj

## 4. Među-zavisnosti provjerene
- results tab
- review queue tab
- controller sloj
- state/viewmodel sloj
- audit run tok
- testovi / ručne provjere

## 5. Rizici koji ostaju
- napiši iskreno ako je neki tab i dalje predebeo
- napiši ako je ostalo nešto za Fazu 5

## 6. Testovi
- koje si pokrenuo
- koji su prošli
- šta treba ručno provjeriti

Ako je nešto blokirano, napiši:

**BLOKIRANO**
- razlog
- fajlovi / slojevi koje blokira
- šta tačno treba razjasniti

---

# 9. Završna napomena

Ovaj zadatak nije “uljepšavanje GUI-a”.

Ovo je disciplinovano razdvajanje odgovornosti, da bi:
- naredne promjene bile jeftinije
- bugovi bili lakši za lociranje
- tabovi prestali biti pretrpani poslovnom logikom

Ako vidiš probleme vezane za:
- category inference
- report generator
- CLI/GUI orchestration
- config reorganizaciju

navedi ih pod **Rizici koji ostaju**, ali ih ne rješavaj ovdje osim ako direktno blokiraju Fazu 3.
