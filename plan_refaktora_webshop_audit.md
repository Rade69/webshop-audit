# Plan refaktora za projekat **WebshopAudit**

Ovaj plan je napravljen tako da se projekat sređuje redoslijedom koji najmanje rizikuje dodatni haos.  
Glavno pravilo je jednostavno:

**prvo konsolidovati podatke i među-zavisnosti, pa tek onda popravljati logiku i GUI.**

Ako se krene obrnutim redoslijedom, GUI će samo maskirati backend probleme, a report sloj će nastaviti da daje nepouzdane rezultate.

---

# 0. Opšti cilj

Cilj refaktora nije samo “očistiti kod”, nego postići sljedeće:

1. da postoji **jedan jedini data contract**
2. da **CLI i GUI koriste isto audit jezgro**
3. da shortlist konačno postane **stvarno koristan**
4. da report generator čita **tačne i aktuelne podatke**
5. da GUI bude **tanji i predvidljiviji**
6. da summary i category logika daju **poslovno smislen rezultat**

---

# 1. Redoslijed faza

## Faza 1 — Konsolidacija data contracta kroz cijeli sistem

### Zašto je prva
Ovo je trenutno najkritičnije usko grlo.  
Ako `extractor`, `scorer`, `report_generator`, `results_controller`, `review_controller` i tabovi ne koriste ista imena i isto značenje kolona, svaki dalji rad je klimav.

### Glavni cilj
Uskladiti:
- canonical nazive kolona
- score/flag kolone
- shape DataFrame-a
- očekivanja GUI sloja
- očekivanja report generatora
- očekivanja CSV eksporta

### Šta ulazi u ovu fazu
- popis svih canonical kolona iz `extractor` i `scorer` sloja
- identifikacija svih zastarjelih aliasa
- uklanjanje starih imena iz GUI kontrolera i report generatora
- provjera da CSV output koristi ista imena
- testovi koji štite data shape

### Rezultat faze
Na kraju faze mora važiti:
- jedno polje = jedno ime = jedno značenje
- GUI ne koristi stara imena
- report generator ne koristi stara imena
- eksport je usklađen sa scorer slojem

### Rizik ako se preskoči
Sve ostalo postaje nepouzdano, posebno:
- filteri u results tabu
- review queue
- summary izvještaji
- DOCX report

---

## Faza 2 — Refaktor shortlist i review logike

### Zašto ide poslije faze 1
Shortlist zavisi od stabilnih score i flag kolona.  
Ako data contract nije sređen, shortlist se ne može ozbiljno popravljati.

### Glavni cilj
Pretvoriti shortlist iz skoro nasumičnog “najnižih N” mehanizma u stvarno koristan model za ljudsku reviziju.

### Šta ulazi u ovu fazu
- analiza postojećeg `manual_review_candidates.csv`
- uvođenje severity logike
- odvajanje:
  - kritičnih stranica
  - sumnjivih stranica
  - niskog scorea
  - ne-produktnih stranica
- reason code-ovi zašto je URL u shortlisti
- deduplikacija i realan broj kandidata
- jasno razdvajanje domain shortlist logike od GUI review workflow-a

### Rezultat faze
Na kraju faze shortlist mora:
- biti manji i korisniji
- imati objašnjive razloge
- ne zatrpavati review queue
- davati pregled stvarno problematičnih stranica

### Rizik ako se preskoči
Korisnik dobija puno buke i malo signala.  
Review queue gubi smisao.

---

## Faza 3 — Razdvajanje GUI prikaza od domain interpretacije

### Zašto tek sad
Kad su podaci i shortlist logika stabilni, može se bezbjedno tanjiti GUI.

### Glavni cilj
Smanjiti količinu logike u tabovima i prebaciti tumačenje podataka tamo gdje pripada:
- controller
- viewmodel/state
- domain sloj

### Šta ulazi u ovu fazu
- refaktor `results_tab.py`
- refaktor `review_queue_tab.py`
- refaktor dijelova `input_tab.py` ako nose previše odgovornosti
- jasnije mapiranje u controller sloju
- manje direktnog rada nad DataFrame-om u samim tabovima
- uklanjanje lokalnih fallbackova koji skrivaju backend problem

### Rezultat faze
Na kraju faze GUI mora biti:
- tanji
- predvidljiviji
- lakši za testiranje
- manje zavisan od “magičnih” pretpostavki

### Rizik ako se preskoči
Svaka iduća promjena na filterima, kolonama i prikazu biće skupa i rizična.

---

## Faza 4 — Usklađivanje report generatora i summary sloja

### Zašto tek poslije prethodnih faza
Report generator je završni sloj.  
Nema smisla sređivati ga dok su podaci i shortlist nestabilni.

### Glavni cilj
Da izvještaji i summary CSV/DOCX sloj budu tačni, dosljedni i poslovno korisni.

### Šta ulazi u ovu fazu
- usklađivanje `report_generator.py` sa canonical kolonama
- uklanjanje pretpostavki o starim poljima
- poboljšanje sitewide summary logike
- poboljšanje category summary logike
- provjera da output nije “lijep ali netačan”

### Rezultat faze
Na kraju faze report mora:
- čitati tačne kolone
- padati glasno ili jasno upozoriti ako nešto nedostaje
- davati summary koji stvarno ima smisla

### Rizik ako se preskoči
Korisnik će vjerovati izvještaju koji može biti podatkovno pogrešan.

---

## Faza 5 — Konsolidacija orchestration sloja između CLI i GUI toka

### Zašto zadnja
Ovo je više arhitektonsko učvršćivanje nego hitni bugfix.  
Ali važno je da CLI i GUI ne nastave evoluirati kao dva odvojena proizvoda.

### Glavni cilj
Svesti audit tok na jedno zajedničko jezgro i izbjeći dupliranje orchestration ponašanja.

### Šta ulazi u ovu fazu
- poređenje `main.py` i `audit/pipeline.py`
- identifikacija duplirane orchestration logike
- jasno razdvajanje:
  - entry point
  - orchestration
  - domain pipeline
- tanji CLI
- tanji GUI controller entry

### Rezultat faze
Na kraju faze:
- CLI i GUI koriste isti pipeline tok
- manje je dupliranog ponašanja
- manje je šanse da bug postoji samo u jednom modu rada

### Rizik ako se preskoči
Vremenom će GUI i CLI davati različite rezultate nad istim ulazom.

---

# 2. Završni redoslijed rada

## Obavezni redoslijed
1. **Faza 1 — Data contract**
2. **Faza 2 — Shortlist/review**
3. **Faza 3 — GUI razdvajanje**
4. **Faza 4 — Report/summary**
5. **Faza 5 — CLI/GUI orchestration konsolidacija**

---

# 3. Šta ne raditi između faza

## Strogo izbjegavati
- dodavanje novih featurea prije završetka faze 1
- popravljanje GUI simptoma bez sređivanja izvora problema
- lokalne alias kolone “samo da proradi”
- novi report detalji dok report generator ne bude usklađen
- dodatne shortlist opcije prije severity modela
- vizuelni polish GUI-a prije logičkog razdvajanja

---

# 4. Definicija uspjeha po fazama

## Faza 1 je završena kad:
- nema više aktivnih zastarjelih alias naziva
- GUI i report čitaju ista canonical polja
- testovi štite shape podataka

## Faza 2 je završena kad:
- shortlist više ne zatrpava review queue
- svaki kandidat ima reason code
- broj kandidata je smislen

## Faza 3 je završena kad:
- tabovi sadrže manje logike
- controller/viewmodel nose veći dio interpretacije
- GUI fallbackovi ne skrivaju backend bugove

## Faza 4 je završena kad:
- report koristi canonical kolone
- category i sitewide summary daju smislen rezultat
- output se može braniti pred korisnikom

## Faza 5 je završena kad:
- CLI i GUI dijele isti orchestration put
- nema značajne duplirane logike između entry point slojeva

---

# 5. Moj iskreni savjet

Najveća greška bi bila da sad odmah kreneš na GUI ili report “jer se to vidi”.  
To je pogrešan redoslijed.

**Prava osnova svega je faza 1.**  
Ako nju uradiš kako treba, sve ostalo postaje mnogo jednostavnije.

Ako je uradiš površno, svaka sljedeća faza će biti skuplja i nestabilnija.

---

# 6. Sljedeći korak

Poslije ovog plana ide:
- **prompt za Fazu 1**
- zatim, tek nakon toga:
- **prompt za Fazu 2**
- pa dalje redom
