# PROMPT — FAZA 4: Usklađivanje report generatora i summary sloja

Radiš na projektu **WebshopAudit**.

Prije rada obavezno pročitaj:
- `AGENTS_webshop_audit.md`
- `CLAUDE_webshop_audit.md`

Ovaj zadatak je **isključivo Faza 4** iz plana refaktora.  
Podrazumijeva se da su:
- **Faza 1** (data contract konsolidacija) završena
- **Faza 2** (shortlist i review logika) završena
- **Faza 3** (GUI razdvajanje) završena

Ne radi Fazu 5.  
Ne radi novi feature development.  
Ne radi GUI redesign.  
Ne mijenjaj scoring ili shortlist semantiku osim ako je minimalno nužno da report i summary sloj budu dosljedni stvarnim podacima.

---

# 1. Cilj zadatka

Cilj je da **report generator i summary sloj budu tačni, dosljedni i poslovno korisni**.

Trenutno report radi i generiše izlaz, ali to nije dovoljno.  
Potrebno je osigurati da:

- report čita **stvarna canonical polja**
- summary metrike budu **dosljedne scorer/shortlist/output sloju**
- category summary ne bude trivijalan i skoro beskoristan
- report ne koristi lokalne pretpostavke koje mogu dati “lijep, ali netačan” izlaz
- output može da se **brani pred korisnikom** kao realna analiza, a ne samo tehnički generisan dokument

---

# 2. Najvažnije pravilo

**Report nije dekoracija.**

Ako report kaže nešto korisniku, to mora biti:
- izvedeno iz stvarnih canonical podataka
- logički tačno
- konzistentno sa CSV outputima
- dovoljno objašnjivo

Nije dozvoljeno da report:
- koristi zastarjele kolone
- lokalno prevodi podatke na način koji mijenja značenje
- prikazuje “smart” zaključke koji nisu podržani stvarnim signalima

---

# 3. Scope — šta tačno radiš

## 3.1. Pregledaj kompletan report tok

Obavezno pregledaj:
- `audit/report_generator.py`
- `audit/exporters.py`
- `audit/scorer.py`
- `audit/shortlist.py`
- `audit/pipeline.py`

Po potrebi pregledaj i:
- output CSV fajlove koje report čita
- helper funkcije vezane za summary ili formatting

Treba da potvrdiš:
- koje kolone report stvarno koristi
- da li su te kolone canonical
- da li report išta “pretpostavlja” umjesto da validira
- da li summary sekcije odgovaraju stvarnom shape-u outputa

---

## 3.2. Uskladi report sa canonical kolonama

Potrebno je da report generator koristi stvarna i stabilna polja iz output sloja.

Posebno provjeri:
- score kolone
- reason / severity kolone
- flags i issue kolone
- schema/HTML signal kolone
- summary kolone po kategoriji

Ako report koristi:
- zastarjelo ime
- fallback koji mijenja značenje
- lokalnu interpretaciju bez validacije

to mora biti popravljeno.

Ako neka kolona nedostaje:
- fail loud ili
- eksplicitno fallback sa upozorenjem

Nikako tihi fallback koji može promijeniti smisao izvještaja.

---

## 3.3. Sredi sitewide summary logiku

Provjeri da li sitewide summary i scorecard zaista odgovaraju:
- scored DataFrame-u
- summary CSV-ovima
- stvarnim count-ovima problema

Potrebno je da report dosljedno izračunava i prikazuje:
- prosječne score vrijednosti
- broj stranica bez cijene
- broj stranica bez schema
- indexability probleme
- fetch greške
- druge ključne aggregate pokazatelje

Ako isti broj postoji na više mjesta u sistemu, moraš izbjeći da report računa svoju paralelnu verziju bez potrebe.

---

## 3.4. Ozbiljno popravi category summary logiku

Ovo je jedan od glavnih ciljeva Faze 4.

Trenutno category summary daje vrlo malu poslovnu vrijednost ako se sve praktično svede na:
- “Proizvodi”

Potrebno je pregledati kako se:
- formira kategorija
- agregira po kategoriji
- prikazuje “bottom 5” ili sličan prikaz

Cilj je da category summary bude:
- stabilniji
- smisleniji
- poslovno korisniji

### Važno
Ako je root problem category inference logika, popravi je na najprirodnijem mjestu:
- u `scorer.py`
- ili u malom domain helper sloju

Ne uvoditi category heuristiku samo u report generatoru ako bi to stvorilo drugi izvor istine.

### Očekivanje
Na kraju category summary ne smije biti samo formalno popunjen, nego treba realno razlikovati kategorije gdje god je to moguće iz dostupnih signala.

---

## 3.5. Uskladi shortlist/report vezu

Pošto je Faza 2 završena, report sada treba korektno koristiti:
- `reasons`
- `reason_count`
- severity
- shortlist prikaz

Provjeri da prilog tipa:
- “Top kandidata za pregled”

zaista prikazuje:
- ispravne razloge
- ispravne oznake
- smislen shortlist prikaz

Ako koristiš human-readable mapiranje reason kodova:
- neka bude dosljedno
- neka ne mijenja značenje
- neka bude centralizovano koliko je razumno

---

## 3.6. Provjeri kvalitet tekstualnih zaključaka

Executive Summary, Quick Wins i drugi tekstualni dijelovi ne smiju zvučati uvjerljivo ako nisu dovoljno potkrijepljeni podacima.

Potrebno je provjeriti:
- da li svaki glavni zaključak ima uporište u metrikama
- da li Quick Wins odgovaraju stvarnim problemima iz uzorka
- da li formulacije ostaju poslovno korisne, ali ne pretjeruju
- da li tekst ne pravi “prevelik skok” iz malog uzorka ka preširokom zaključku

### Pravilo
Bolje je imati:
- kraći, tačan zaključak

nego:
- impresivan, ali preuveličan zaključak

---

## 3.7. Dodaj validacije i testove

Dodaj ili ažuriraj testove tako da štite:

- report koristi canonical kolone
- report ne puca na praznim / NaN / miješanim vrijednostima
- summary brojevi odgovaraju ulaznim podacima
- shortlist prilog koristi reason/severity ispravno
- category summary radi konzistentno za realne i rubne slučajeve
- tekstualni dijelovi ne pucaju kad neki podatak nedostaje

---

# 4. Među-zavisnosti koje moraš obavezno provjeriti

Ako mijenjaš report i summary sloj, moraš provjeriti uticaj na:

1. **`audit_report.docx`**
   - sve glavne sekcije
   - scorecard
   - ključne metrike
   - quick wins
   - prilog shortlist kandidata

2. **CSV output**
   - da report koristi stvarni output, ne alternativnu internu verziju

3. **`category_summary.csv`**
   - da je semantički koristan
   - da nije trivijalno popunjen bez stvarne analitičke vrijednosti

4. **`manual_review_candidates.csv`**
   - da reasons/severity prikaz ostane dosljedan

5. **`best_products_sample.csv`**
   - da se ne pokvari indirektno ako ga report koristi

6. **Scorer / summary logika**
   - da report ne uvede drugi izvor istine

---

# 5. Šta je dozvoljeno, a šta nije

## Dozvoljeno
- refaktor `report_generator.py`
- manje dopune u `scorer.py` ili helper sloju za category/site summary ako je to pravo mjesto
- centralizacija mapiranja za report prikaz
- validacije kolona i shape-a
- testovi za report i summary ponašanje

## Nije dozvoljeno
- mijenjati canonical data contract bez jakog razloga
- mijenjati shortlist model
- mijenjati score težine ili scoring strategiju
- raditi GUI refaktor
- raditi CLI/GUI orchestration redesign
- generisati “pametnije” tekstove koji nisu podržani podacima

---

# 6. Kriterij uspjeha

Zadatak je završen tek kad su ispunjeni svi uslovi:

- report koristi canonical kolone i stabilan data put
- summary brojevi su dosljedni stvarnim outputima
- category summary daje više od trivijalnog “Proizvodi”
- shortlist prilog je tačan i objašnjiv
- tekstualni zaključci su korisni, ali ne preuveličani
- report sloj je robusniji na prazne i rubne slučajeve
- testovi štite glavni report tok

---

# 7. Testovi

Dodaj ili ažuriraj testove tako da štite:

- generisanje reporta sa canonical output podacima
- ponašanje kada neke tekstualne kolone imaju NaN
- shortlist prilog sa reason/severity kolonama
- category summary za više kategorija
- fallback / validacija kad neka kolona nedostaje
- konzistentnost scorecard agregata

Ako nemaš pun DOCX end-to-end test:
- napiši šta je pokriveno funkcionalnim testovima
- šta je statički provjereno
- šta treba ručno potvrditi generisanjem reporta

---

# 8. Očekivani izlaz od tebe

Vrati odgovor u ovom formatu:

## 1. Šta je bilo problematično u prethodnoj verziji
- kratko i iskreno

## 2. Šta je sada promijenjeno
- kratko i jasno

## 3. Pogođeni fajlovi
- kompletan spisak

## 4. Šta je popravljeno u report sloju
- canonical kolone
- shortlist prikaz
- summary brojevi
- tekstualni zaključci

## 5. Šta je urađeno za category summary
- gdje sada živi logika
- kako se kategorije izvlače
- zašto je bolje nego prije

## 6. Među-zavisnosti provjerene
- `audit_report.docx`
- `category_summary.csv`
- `manual_review_candidates.csv`
- `best_products_sample.csv`
- scorer / pipeline / output tok
- testovi

## 7. Rizici koji ostaju
- napiši iskreno šta još nije idealno
- posebno ako nešto ostaje za Fazu 5

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

Ovaj zadatak nije “napiši ljepši report”.

Ovo je:
- usklađivanje report generatora sa stvarnim podacima
- jačanje summary sloja
- popravljanje analitičke vrijednosti izvještaja

Ako vidiš probleme vezane za:
- CLI/GUI orchestration
- config reorganizaciju
- dublju arhitekturu pipeline-a

navedi ih pod **Rizici koji ostaju**, ali ih ne rješavaj ovdje osim ako direktno blokiraju Fazu 4.
