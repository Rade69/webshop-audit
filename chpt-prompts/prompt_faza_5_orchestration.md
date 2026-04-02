# PROMPT — FAZA 5: Konsolidacija orchestration sloja između CLI i GUI toka

Radiš na projektu **WebshopAudit**.

Prije rada obavezno pročitaj:
- `AGENTS_webshop_audit.md`
- `CLAUDE_webshop_audit.md`

Ovaj zadatak je **isključivo Faza 5** iz plana refaktora.  
Podrazumijeva se da su:
- **Faza 1** (data contract konsolidacija) završena
- **Faza 2** (shortlist i review logika) završena
- **Faza 3** (GUI razdvajanje) završena
- **Faza 4** (report i summary sloj) završena

Ne radi novi feature development.  
Ne radi GUI redesign.  
Ne mijenjaj scoring, shortlist ili report semantiku osim ako je minimalno nužno da orchestration tok bude jedinstven i čist.

---

# 1. Cilj zadatka

Cilj je da **CLI i GUI koriste isto audit jezgro i isti orchestration put** koliko god je to razumno moguće.

Trenutni rizik je da:
- `main.py`
- `audit/pipeline.py`
- GUI controlleri za pokretanje audita

mogu postepeno evoluirati u više različitih tokova rada.

To vodi do problema:
- isti ulaz ne daje isti izlaz u CLI i GUI modu
- bug se pojavi samo u jednom entry pointu
- popravke se rade na dva mjesta
- održavanje postaje skupo i zbunjujuće

Na kraju rada treba biti jasno:
- gdje je **jedini orchestration source-of-truth**
- šta su samo entry point slojevi
- kako GUI i CLI ulaze u isti glavni tok

---

# 2. Najvažnije pravilo

**CLI i GUI ne smiju imati paralelnu poslovnu logiku za audit tok.**

To znači:
- GUI ne smije imati svoju posebnu verziju pipeline ponašanja
- CLI ne smije imati skriveni “drugi audit engine”
- orchestration mora biti centralizovan
- entry point slojevi smiju samo prikupljati input, pozvati tok i prikazati rezultat

---

# 3. Scope — šta tačno radiš

## 3.1. Identifikuj sve entry pointove i orchestration tokove

Obavezno pregledaj:
- `main.py`
- `audit/pipeline.py`
- `gui/controllers/audit_run_controller.py`

Po potrebi pregledaj i:
- `gui/main_window.py`
- `gui/app_state.py`
- helper funkcije koje pokreću audit run
- export/report pozive iz GUI toka
- CLI argument parsing i workflow

Treba da potvrdiš:
- šta tačno radi `main.py`
- šta tačno radi `audit/pipeline.py`
- šta tačno radi GUI run controller
- gdje se duplira logika
- gdje se razlikuje redoslijed koraka
- gdje se razlikuje error handling
- gdje se razlikuje export/report poziv

---

## 3.2. Definiši jedan zajednički orchestration tok

Potrebno je da postoji **jedan glavni tok** koji obavlja:

1. pripremu ulaza
2. sitemap / URL discovery
3. fetch + extraction
4. scoring
5. shortlist generation
6. export outputa
7. opcionalno report generation
8. povrat strukturiranog rezultata

Taj glavni tok treba živjeti na jednom prirodnom mjestu, najvjerovatnije:
- `audit/pipeline.py`
ili
- malom orchestration servisnom sloju ako je to čišće

Ali ne smije završiti razbacan između:
- CLI
- GUI controllera
- helper funkcija

---

## 3.3. Svedi CLI na pravi entry point

CLI treba da:
- parsira argumente
- validira osnovni input
- pozove zajednički orchestration tok
- prikaže / loguje rezultat
- izađe sa smislenim statusom

CLI ne treba da:
- duplira audit korake
- posebno računa shortlist
- posebno zove report/export logiku ako to već radi zajednički tok
- uvodi vlastitu verziju default vrijednosti bez razloga

---

## 3.4. Svedi GUI run controller na pravi entry point/orchestrator adapter

GUI controller treba da:
- prikupi input iz GUI sloja
- pozove zajednički orchestration tok
- prati progres i status za UI
- preda rezultat state/view sloju

GUI controller ne treba da:
- implementira svoju verziju pipeline logike
- ručno ponavlja korake koje već radi zajednički tok
- direktno postaje drugi audit engine

Ako GUI ima specifične potrebe:
- progress callbacks
- signal emission
- cancellation hooks

to treba dodati tako da **ne razbije zajedničko jezgro**.

---

## 3.5. Uskladi konfiguraciju i defaulte

Ako CLI i GUI imaju različite default vrijednosti za:
- timeout
- retries
- broj radnika
- report generation
- shortlist/export opcije

provjeri da li je to:
- namjerno
- opravdano
- ili slučajan drift

Cilj je da shared orchestration koristi:
- zajednički config
- jasno definisane override opcije
- što manje skrivenih default razlika

---

## 3.6. Uskladi error handling i rezultat izvršavanja

CLI i GUI mogu drugačije **prikazivati** grešku, ali ne bi smjeli drugačije **izvršavati** audit bez razloga.

Potrebno je da zajednički tok:
- vraća strukturirani rezultat
- jasno prijavljuje greške / djelimične greške
- bude dovoljno neutralan da ga mogu koristiti i CLI i GUI

Ako postoje razlike u:
- try/except granicama
- export ponašanju
- report generisanju
- partial success handlingu

to treba uskladiti koliko je moguće.

---

## 3.7. Ne miješaj ovo sa drugim fazama

Ako vidiš:
- category inference problem
- scoring problem
- report sadržaj problem
- GUI polish problem

to nije tema ove faze osim ako direktno blokira orchestration konsolidaciju.

---

# 4. Među-zavisnosti koje moraš obavezno provjeriti

Ako konsoliduješ orchestration sloj, moraš provjeriti uticaj na:

1. **CLI tok**
   - pokretanje iz komandne linije
   - argumenti
   - izlazni fajlovi
   - status završetka

2. **GUI audit run tok**
   - pokretanje audita iz aplikacije
   - progres
   - prikaz rezultata
   - review queue i report putanju nakon run-a

3. **`audit/pipeline.py`**
   - da postane ili ostane jasan source-of-truth

4. **Export / report**
   - da se i dalje generišu kada treba
   - da nema duplog pozivanja

5. **Config / default ponašanje**
   - da nema skrivenih razlika između GUI i CLI moda bez objašnjenja

6. **Testovi**
   - da su pogođeni entry pointovi pokriveni koliko je razumno moguće

---

# 5. Šta je dozvoljeno, a šta nije

## Dozvoljeno
- refaktor `main.py`
- refaktor `audit/pipeline.py`
- refaktor `gui/controllers/audit_run_controller.py`
- uvođenje malog shared orchestration API-ja / rezultata ako je potrebno
- usklađivanje config/default ponašanja
- testovi za shared run tok i entry point ponašanje

## Nije dozvoljeno
- mijenjati canonical data contract
- mijenjati scoring/shortlist/report semantiku
- raditi novi GUI feature set
- raditi veliki arhitektonski rewrite cijelog projekta
- uvoditi previše apstrakcije bez jasne koristi
- skrivati postojeće tehničke dugove pod “orchestration refaktor”

---

# 6. Kriterij uspjeha

Zadatak je završen tek kad su ispunjeni svi uslovi:

- postoji jasan shared orchestration put
- CLI i GUI ulaze u isti audit tok
- nema značajne duplirane business logike između entry pointova
- config/default ponašanje je usklađenije i jasnije
- error handling i rezultat izvršavanja su konzistentniji
- glavni tok i dalje radi i kroz CLI i kroz GUI
- kod je jednostavniji za održavanje nego prije

---

# 7. Testovi

Dodaj ili ažuriraj testove tako da štite:

- shared orchestration tok
- CLI entry ponašanje
- GUI run controller ponašanje u odnosu na shared tok
- da export/report nisu slučajno pozvani dvaput
- da structured rezultat izvršavanja ostane stabilan
- da greške i partial success scenariji imaju konzistentno ponašanje

Ako nemaš pun integration test za GUI runtime:
- napiši šta je pokriveno unit/integration testovima
- šta je statički provjereno
- šta treba ručno provjeriti kroz stvarni run

---

# 8. Očekivani izlaz od tebe

Vrati odgovor u ovom formatu:

## 1. Šta je bilo problematično prije
- gdje je bila duplirana logika
- gdje su CLI i GUI išli različitim putem

## 2. Šta je sada promijenjeno
- kratko i jasno

## 3. Pogođeni fajlovi
- kompletan spisak

## 4. Gdje sada živi shared orchestration tok
- tačno mjesto
- šta radi
- ko ga poziva

## 5. Kako sada rade entry pointovi
- CLI
- GUI audit controller

## 6. Među-zavisnosti provjerene
- CLI run
- GUI run
- export/report tok
- config/default ponašanje
- testovi

## 7. Rizici koji ostaju
- napiši iskreno šta još nije idealno
- posebno šta ostaje kao tehnički dug van scope-a Faze 5

## 8. Testovi
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

Ovaj zadatak nije “napravi još slojeva”.

Ovo je:
- konsolidacija jednog audit toka
- smanjenje duplirane logike
- stabilizacija ponašanja između CLI i GUI moda

Ako vidiš druge probleme koji nisu direktno u orchestration sloju, navedi ih pod **Rizici koji ostaju**, ali ih ne rješavaj ovdje osim ako direktno blokiraju Fazu 5.
