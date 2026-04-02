# PROMPT — Stabilizacija 4: End-to-end testovi

Radiš na projektu **WebshopAudit**.

Prije rada obavezno pročitaj:
- `AGENTS_webshop_audit.md`
- `CLAUDE_webshop_audit.md`

Ovo nije nova velika refaktor faza.  
Ovo je **stabilizacioni zadatak #4: end-to-end testovi**.

Ne radi config cleanup.  
Ne radi GUI redesign.  
Ne radi nove featuree.  
Ne mijenjaj scoring, shortlist, report ili category semantiku osim ako je minimalno nužno da bi testovi mogli pouzdano zaštititi postojeće ponašanje.

---

# 1. Cilj zadatka

Cilj je da se uvede **mali broj jakih end-to-end i integration testova** koji štite glavni životni ciklus aplikacije.

Do sada je dosta toga refaktorisano i stabilizovano:
- data contract
- shortlist/review logika
- GUI adapter sloj
- report generator i summary
- shared orchestration između CLI i GUI toka
- category inference
- sample bucket tuning

Sada to treba zaključati testovima tako da se kasnije ne raspadne kroz male izmjene.

Na kraju rada treba da važi:

- glavni tok audit run-a je pokriven testovima
- ključni output fajlovi i njihove semantike su zaštićeni
- shortlist/report konzistentnost je testirana
- shared orchestration put je testiran
- ne oslanjamo se samo na ručne smoke testove

---

# 2. Najvažnije pravilo

**Ne praviti 100 sitnih testova koji štite internu implementaciju.**

Treba nam:
- mali broj jačih testova
- testovi koji štite stvarno ponašanje sistema
- testovi koji hvataju regresije na nivou glavnog toka

Bolje je imati:
- 5–10 jakih integration/end-to-end testova

nego:
- 50 trivijalnih testova koji ne hvataju stvarne kvarove

---

# 3. Scope — šta tačno radiš

## 3.1. Pregledaj postojeće testove i pokrivenost

Obavezno pregledaj:
- `tests/` strukturu
- postojeće testove za:
  - pipeline
  - scorer
  - shortlist
  - GUI controllers
  - report generator ako postoje

Treba da potvrdiš:
- šta je već dobro pokriveno
- šta još nije pokriveno na nivou glavnog toka
- gdje nedostaje test koji spaja više slojeva

---

## 3.2. Dodaj end-to-end / integration test za shared audit run

Treba postojati test koji pokriva glavni audit lifecycle na malom, kontrolisanom ulazu:

- discovery / URL input
- extraction
- scoring
- shortlist
- export
- summary output

Ne mora koristiti realni internet fetch ako to čini test krhkim.  
Ali mora testirati **stvarni orchestration put**, ne samo izolovane funkcije.

Ako koristiš fixture/fake input:
- neka bude dovoljno realan
- neka proizvodi više vrsta outputa
- neka omogući provjeru smislenog CSV izlaza

---

## 3.3. Dodaj test za output shape i ključne fajlove

Treba zaštititi da audit run proizvodi i održava očekivane ključne outpute, npr:

- `products_raw.csv`
- `products_scored.csv`
- `manual_review_candidates.csv`
- `best_products_sample.csv`
- `category_summary.csv`
- `errors.csv`

Ne mora svaki test provjeravati svaku kolonu, ali mora provjeriti:
- da fajlovi nastaju
- da nisu prazni kad ne trebaju biti
- da imaju ključne canonical kolone
- da su međusobno semantički konzistentni

---

## 3.4. Dodaj test za shortlist/report konzistentnost

Treba postojati test koji štiti odnos između:
- `manual_review_candidates.csv`
- report shortlist priloga / podataka koji hrane report

Cilj:
- razlog i severity moraju ostati konzistentni
- sample kandidati moraju ostati jasno označeni
- stvarni issue kandidati moraju ostati prioritetni

Ovdje ne moraš nužno parsirati cijeli DOCX ako to previše otežava test.  
Možeš testirati niži sloj koji report koristi za pripremu tih sekcija, ali mora biti dovoljno blizu stvarnom outputu.

---

## 3.5. Dodaj test za category summary konzistentnost

Treba zaštititi da:
- `category_summary.csv` nije trivijalno generički kad postoje bolji signali
- generičke kategorije ne pregaze korisne kategorije
- fallback `Unknown` radi gdje treba
- report/category summary sloj koristi iste podatke

Ovo ne mora biti “AI test”, nego deterministički integration test sa kontrolisanim inputom.

---

## 3.6. Dodaj test za CLI/shared orchestration tok

Pošto je Faza 5 konsolidovala CLI i GUI preko istog `run_audit()` toka, treba imati test koji štiti da:
- CLI entry point poziva shared orchestration
- shared rezultat ostaje stabilan
- export/report se ne pozivaju dvaput
- config/default ponašanje ne ode u drugi smjer

Ako puni CLI subprocess test bude pretežak, dozvoljen je test entry sloja i poziva shared toka, ali mora štititi stvarno ponašanje, ne samo import.

---

## 3.7. GUI integration gdje je razumno

Ne treba raditi teško, sporo GUI end-to-end testiranje svega.  
Ali treba zaštititi bar najvažnije tokove gdje ima smisla:

- load results
- load review queue
- selection/details prikaz kroz adapter sloj
- da adapter setup i dalje radi u glavnom toku

To može biti:
- integration test controller + viewmodel + prepared data
- bez punog klikanja kroz svaki widget, ako to pravi previše krhkosti

---

# 4. Među-zavisnosti koje moraš obavezno provjeriti

Ako uvodiš end-to-end testove, moraš provjeriti uticaj na:

1. **Shared orchestration**
   - `run_audit()` kao source-of-truth
   - CLI i GUI entry očekivanja

2. **Output fajlovi**
   - shape
   - canonical kolone
   - konzistentnost među fajlovima

3. **Shortlist**
   - issue vs sample odnos
   - reasons/severity

4. **Category summary**
   - korisnost i stabilnost

5. **Report pripremu**
   - ne nužno puni DOCX parsing, ali barem data feed za report sekcije

6. **Test runtime**
   - testovi ne smiju biti toliko spori i krhki da ih niko neće pokretati

---

# 5. Šta je dozvoljeno, a šta nije

## Dozvoljeno
- uvođenje integration/end-to-end testova
- test fixtures za mali, realističan kontrolisani dataset
- manje prilagodbe helper sloja da testiranje bude moguće
- minimalne izmjene u kodu ako su potrebne da se dobiju testabilni shared result objekti

## Nije dozvoljeno
- veliki rewrite aplikacije radi testova
- mijenjanje poslovne semantike samo da test prođe
- uvoditi teške, nestabilne testove koji zavise od stvarnog interneta bez potrebe
- pretvarati ovo u GUI automation projekat
- zamijeniti smislen integration test sa gomilom mock-only testova

---

# 6. Kriterij uspjeha

Zadatak je završen tek kad su ispunjeni svi uslovi:

- postoji mali skup jakih integration/end-to-end testova
- glavni audit lifecycle je pokriven
- output fajlovi i data contract su djelimično zaključani testovima
- shortlist/report/category konzistentnost je pokrivena
- shared orchestration tok je testiran
- testovi su dovoljno stabilni i brzi da imaju praktičnu vrijednost

---

# 7. Testovi koje očekujem da uvedeš

Ne moraš ih nazvati baš ovako, ali očekujem pokrivanje barem ovih scenarija:

1. **shared audit run integration**
2. **output files shape integration**
3. **manual_review_candidates semantics**
4. **category_summary semantics**
5. **report input consistency**
6. **CLI/shared orchestration integration**
7. **results/review adapter integration** (u mjeri koja je razumna)

---

# 8. Očekivani izlaz od tebe

Vrati odgovor u ovom formatu:

## 1. Šta je nedostajalo u test pokrivenosti
- kratko i iskreno

## 2. Šta je sada dodano
- kratko i jasno

## 3. Pogođeni fajlovi
- kompletan spisak

## 4. Koji glavni tokovi su sada pokriveni
- audit run
- output fajlovi
- shortlist
- category summary
- shared orchestration
- GUI integration gdje je pokriveno

## 5. Među-zavisnosti provjerene
- data contract
- output shape
- shortlist/report odnos
- category summary
- CLI/shared orchestration
- test runtime stabilnost

## 6. Rizici koji ostaju
- napiši iskreno šta još nije idealno
- posebno ako nešto ostaje za config cleanup ili dokumentaciju

## 7. Testovi
- koje si dodao
- koje si pokrenuo
- koji su prošli
- koliko test suite sada traje
- šta i dalje treba ručno provjeriti

Ako je nešto blokirano, napiši:

**BLOKIRANO**
- razlog
- šta tačno treba razjasniti

---

# 9. Završna napomena

Ovaj zadatak nije “dodaj još testova”.

Ovo je:
- zaključavanje stabilizovanog sistema
- zaštita od regresija
- prijelaz iz faze refaktora u fazu sigurnijeg daljeg razvoja
