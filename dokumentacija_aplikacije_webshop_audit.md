# Dokumentacija aplikacije — Python alat za početni audit web shopa

## Svrha dokumenta

Ovaj dokument objašnjava kako aplikacija radi iz ugla:
- korisnika
- funkcionalne logike
- internog toka obrade
- i očekivanih izlaza

Dokument je pisan tako da bude koristan i kao:
- korisničko uputstvo
- interni projektni pregled
- osnova za buduću tehničku dokumentaciju

---

# 0. Zašto ova aplikacija postoji

Načini na koje kupci pronalaze proizvode se mijenjaju.

Sve više korisnika koristi AI asistente — ChatGPT, Perplexity, Google AI Overview i slične — za pronalazak i poređenje proizvoda. Umjesto da sami pretražuju Google i otvaraju desetine stranica, postavljaju pitanje agentu i dobijaju direktan odgovor s linkovima ka relevantnim produktima.

Ovo nije daleka budućnost. To se već dešava.

Agenti koji odgovaraju na takve upite ne čitaju stranice kao čovjek. Oni čitaju strukturirane podatke, schema markup, kompletnost opisa i jasnoću informacija. Webshop koji ima uredno popunjene schema podatke, jasnu cijenu, dostupnost i opis — ima realno veće šanse da bude prepoznat i preporučen.

Webshop koji ima lijepe slike ali nema Product schema, nema SKU, nema jasnu cijenu u strukturiranom obliku — agent ga ili propušta ili rangira niže.

Ova aplikacija pomaže da se utvrdi gdje webshop stoji u tom kontekstu:
- koje stranice su mašinski čitljive
- gdje nedostaju kritični podaci
- šta treba popraviti da shop bude bolje pozicioniran u novim kanalima distribucije

Jednostavno rečeno:

> Aplikacija pomaže webshopovima da postanu razumljivi AI agentima koji sve više utiču na to koji proizvod kupac uopće vidi.

---

# 1. Šta je ova aplikacija

Ova aplikacija je desktop alat za **početni audit web shopa**.

Njena glavna svrha nije da zamijeni ručni audit, nego da:
- automatski prikupi veći broj podataka sa product stranica
- pronađe očigledne tehničke i sadržajne signale
- izračuna početne score vrijednosti
- izdvoji problematične proizvode za ručni pregled
- ubrza pripremu audita webshopa

Jednostavno rečeno:

> Aplikacija pomaže da se iz velikog broja product stranica brzo izdvoje one koje vrijedi detaljnije pregledati.

---

# 2. Šta aplikacija nije

Važno je razumjeti i ograničenja.

Aplikacija nije:
- potpuni SEO alat
- potpuni crawler za sve vrste stranica
- alat koji savršeno razumije svaki webshop
- zamjena za ručni UX ili content audit
- sistem koji daje “konačnu istinu” o kvalitetu shopa

Njena uloga je:

> **data collection + signal generation + shortlist alat**

To znači da daje početni signal, a ne finalnu presudu.

---

# 3. Instalacija i pokretanje

## Zahtjevi

- Python 3.11 ili noviji
- pip

## Instalacija

```bash
# 1. Raspakovati zip i ući u direktorij
cd webshop_audit

# 2. Instalirati zavisnosti
pip install -r requirements.txt
```

## Pokretanje GUI moda

```bash
python -m gui.gui_main
```

## Pokretanje CLI moda

```bash
# Iz sitemap URL-a
python main.py --sitemap https://example.com/sitemap.xml --max-urls 300

# Iz domena (auto-discovery sitemap-a)
python main.py --domain https://example.com --max-urls 300

# Iz fajla sa URL-ovima
python main.py --urls-file inputs/urls.txt

# Async mod za veće kataloge
python main.py --domain https://example.com --async --max-concurrent 20
```

## Async mod

Za veće kataloge (500+ URL-ova) preporučuje se async mod koji fetchuje
stranice paralelno umjesto jednu po jednu.

Parametri:
- `--async` — uključuje async fetch
- `--max-concurrent N` — broj paralelnih zahtjeva (default: 10)
- `--batch-delay S` — pauza između batch-eva u sekundama (default: 0.1)

U GUI modu async opcija se bira u Input tabu ako je dostupna.

**Napomena:** Async mod treba koristiti pažljivo. Previše paralelnih
zahtjeva može uzrokovati da server privremeno blokira IP adresu.
Preporučena vrijednost za `--max-concurrent` je između 5 i 15.

---

# 4. Glavna ideja rada aplikacije

Aplikacija radi kroz linearan tok:

```text
URL kolekcija → Fetch → Parse HTML → Extract schema → Score → Shortlist → Export
```

To znači:

1. aplikacija prikupi listu URL-ova
2. preuzme sadržaj stranica
3. izvuče osnovne HTML podatke
4. izvuče structured data / schema podatke
5. izračuna score i zastavice problema
6. formira shortlist za ručni pregled
7. izveze rezultate u fajlove

---

# 4. Glavni korisnički tok

Iz perspektive korisnika, aplikacija radi ovako:

## Korak 1 — unos izvora URL-ova
Korisnik unosi:
- sitemap URL
ili
- domen
ili
- ručnu listu URL-ova
ili
- fajl sa URL-ovima

## Korak 2 — podešavanje run opcija
Korisnik podešava:
- maksimalan broj URL-ova
- delay između zahtjeva
- output folder
- eventualno druge napredne opcije ako postoje

## Korak 3 — pokretanje skeniranja
Korisnik klikne **Start Scan**.

## Korak 4 — praćenje procesa
Na Run tabu korisnik vidi:
- status rada
- trenutnu fazu pipeline-a
- broj obrađenih URL-ova
- broj grešaka
- log poruke

## Korak 5 — pregled rezultata
Na Results tabu korisnik vidi:
- tabelu rezultata
- score kolone
- flags
- detalje za izabrani proizvod
- filtere

## Korak 6 — ručni pregled prioritetnih slučajeva
Na Review Queue tabu korisnik vidi:
- proizvode koje treba ručno pregledati
- razlog zašto su tu
- status pregleda
- note

## Korak 7 — izvoz i dalji rad
Korisnik može:
- otvoriti output folder
- izvesti selektovane rezultate
- otvoriti raw podatke
- nastaviti ručni audit van aplikacije

---

# 5. Objašnjenje po tabovima

---

## 5.1. Input tab

### Svrha
Input tab služi za pripremu skeniranja.

### Šta korisnik tu radi
- unosi sitemap URL
- unosi domen
- ručno lijepi URL-ove
- učitava `.txt` ili `.csv` listu
- bira osnovne opcije run-a

### Ključna polja
- **Sitemap URL** — direktni URL do sitemap XML fajla
- **Domain** — osnovni domen iz kojeg se može pokušati otkriti sitemap
- **URL list** — ručni ili fajl-based unos product URL-ova
- **Max URLs** — gornja granica koliko URL-ova će alat obraditi
- **Delay** — pauza između zahtjeva
- **Output directory** — lokacija gdje će rezultati biti snimljeni

### Šta korisnik dobija kao povratnu informaciju
- broj učitanih URL-ova
- osnovni status inputa
- preview URL-ova
- da li je input spreman za scan

### Ključna svrha ovog taba
Da korisnik prije pokretanja jasno zna:
- šta aplikacija skenira
- odakle su URL-ovi došli
- koje opcije će biti korištene

---

## 5.2. Run / Progress tab

### Svrha
Ovaj tab prikazuje tok izvršavanja skeniranja.

### Šta korisnik tu vidi
- da li aplikacija trenutno radi
- u kojoj je fazi rada
- koliko je URL-ova obrađeno
- koliko je neuspjelih pokušaja
- log poruke i upozorenja

### Tipične informacije na ovom tabu
- **Status**: idle / running / paused / completed / failed
- **Phase**: URL collection / Fetch / Parse HTML / Extract schema / Score / Shortlist / Export
- **Processed URLs**
- **Errors**
- **Elapsed time**
- **Non-product pages**
- **Manual review candidates**

### Zašto je ovaj tab važan
Bez njega korisnik ne zna:
- da li alat radi ispravno
- da li je zapeo
- da li ima puno grešaka
- i koliko će još trajati

---

## 5.3. Results tab

### Svrha
Results tab je glavni radni ekran za pregled prikupljenih rezultata.

### Šta korisnik tu vidi
- tabelu obrađenih proizvoda
- score po dimenzijama
- flags i probleme
- detalje selektovanog proizvoda
- filtere za sužavanje pregleda

### Tipične kolone
- Product / URL
- Catalog Score
- Machine Score
- Commerce Score
- Overall Score
- Flags
- Review Status

### Detalji selektovanog proizvoda
Kada korisnik klikne jedan red, desni panel prikazuje:
- URL
- Title
- H1
- Canonical
- Robots
- Schema status
- Price status
- Availability
- SKU
- GTIN
- Shipping signal
- Returns signal
- Missing fields
- Indexability flags
- Notes

### Zašto je ovaj tab ključan
Ovo je mjesto gdje korisnik:
- prepoznaje probleme
- poredi proizvode
- filtrira rezultate
- odlučuje šta ide u ručni review

---

## 5.4. Review Queue tab

### Svrha
Review Queue je tab za ručni operativni pregled prioritizovanih proizvoda.

### Razlika u odnosu na Results
Results prikazuje širu sliku.
Review Queue prikazuje samo ono što traži ručni pregled.

### Šta korisnik tu vidi
- listu kandidata za ručni review
- razlog zašto su u queue-u
- trenutni review status
- note
- osnovne detalje proizvoda

### Tipični razlozi za ulazak u queue
- missing schema
- missing price
- low content
- noindex
- canonical issue
- suspicious row
- ručno dodan kandidat

### Šta korisnik radi u ovom tabu
- otvara stranicu
- označava status
- dodaje napomenu
- prelazi na sljedeći kandidat
- uklanja proizvod iz queue-a ako više nije relevantan

### Ključna svrha ovog taba
Da audit ne ostane samo u tabeli, nego da postoji:
- konkretan radni red
- jasan razlog
- jasan tok ručne provjere

---

# 6. Kako aplikacija interno radi

---

## 6.1. URL kolekcija

Aplikacija najprije formira listu URL-ova.

To može raditi iz:
- sitemap-a
- domena
- ručne liste
- fajla

Ako se koristi sitemap:
- aplikacija preuzima sitemap XML
- parsira URL-ove
- po potrebi prolazi kroz child sitemap fajlove
- filtrira vjerovatne product URL-ove

Rezultat ove faze je:
- lista URL-ova koja ide u sljedeću fazu

---

## 6.2. Fetch faza

Za svaki URL alat pokušava preuzeti HTML.

U ovoj fazi bilježi:
- originalni URL
- finalni URL
- HTTP status code
- response time
- headers
- greške ako ih ima

Ako fetch ne uspije:
- URL se ne ruši cijeli run
- greška se zapisuje
- alat nastavlja dalje

Ovo je važno jer jedan loš URL ne smije zaustaviti cijeli proces.

---

## 6.3. Parse HTML faza

Nakon uspješnog fetch-a alat iz HTML-a pokušava izvući osnovne signale.

Tipični HTML signali:
- title
- meta description
- H1
- canonical
- robots meta
- breadcrumb tekst
- dužina vidljivog teksta
- broj slika
- mogući price signal
- shipping signal
- returns signal

Ova faza ne pokušava “razumjeti sadržaj kao čovjek”, nego:
- izvlači signalne podatke
- mjeri prisutnost
- mjeri osnovnu kompletnost

---

## 6.4. Extract schema faza

Aplikacija zatim pokušava izvući JSON-LD / schema podatke.

Tipično traži:
- Product schema
- Offer schema

Iz njih pokušava dobiti:
- schema name
- schema description
- schema SKU
- schema GTIN
- schema brand
- schema price
- schema currency
- schema availability

Ova faza je važna jer pokazuje:
- koliko je stranica mašinski čitljiva
- koliko product podaci postoje u strukturisanom obliku

---

## 6.5. Formiranje jedinstvenog zapisa po stranici

HTML i schema podaci se kombinuju u jedan standardizovani zapis.

Taj zapis predstavlja:
- jedan URL
- jedan skup audit signala
- jednu jedinicu za dalje scoring i filtriranje

To je osnova za:
- CSV izvoz
- score računanje
- shortlist logiku
- prikaz u GUI tabeli

---

## 6.6. Scoring faza

Aplikacija zatim računa score vrijednosti.

### Osnovne dimenzije
- **Catalog Score**
- **Machine Score**
- **Commerce Score**

### Šta svaka dimenzija mjeri

#### Catalog Score
Mjeri HTML prisutnost i osnovnu kompletnost, npr:
- title
- H1
- meta
- breadcrumb
- HTML price signal
- vidljivi tekst

#### Machine Score
Mjeri structured data i mašinsku čitljivost, npr:
- Product schema
- Offer schema
- price
- currency
- availability
- SKU
- brand
- GTIN
- canonical

#### Commerce Score
Mjeri osnovne buyer signale, npr:
- price prisutnost
- dovoljno product slika
- shipping signal
- returns signal

### Overall Score
Ukupan score nastaje kao ponderisana kombinacija ove tri dimenzije:

```
Overall = Catalog x 0.35 + Machine x 0.40 + Commerce x 0.25
```

**Zašto Machine Score ima najveću težinu (40%)?**

Zato što je machine readability — prisustvo strukturiranih podataka —
najdirektniji signal za AI agente i shopping sisteme. Stranica koja
ima savršen HTML opis ali nema Product schema teže će biti prepoznata
od strane automatizovanih sistema nego stranica sa kompletnim schema
podacima i kraćim opisom.

Ovo odražava primarnu svrhu alata: pripremu webshopa za mašinsku
čitljivost, ne samo za ljudskog posjetitelja.

Važno:
- score nije „končna istina”
- score je heuristički signal
- služi za početno rangiranje i filtriranje

---

## 6.7. Flag detection

Pored score-a, alat izdvaja i posebne signale problema.

Primjeri:
- missing schema
- missing price
- suspicious low content
- canonical mismatch
- noindex
- indexability blockers
- missing fields

To je važno jer često:
- problem nije samo nizak score
- nego konkretna vrsta greške koju korisnik treba vidjeti odvojeno

---

## 6.8. Shortlist logika

Nakon scoring-a alat izdvaja proizvode za ručni pregled.

To radi na osnovu:
- niskog overall score-a
- kritičnih flagova
- nedostajućih važnih polja
- sumnjivih signala

Rezultat je:
- lista proizvoda koje vrijedi pogledati ručno

To štedi vrijeme jer korisnik ne mora ručno otvarati cijeli katalog.

---

## 6.9. Export faza

Na kraju aplikacija izvozi rezultate u fajlove.

Tipični output fajlovi:
- `products_raw.csv`
- `products_scored.csv`
- `manual_review_candidates.csv`
- `best_products_sample.csv`
- `non_product_pages.csv`
- `category_summary.csv`
- `errors.csv`
- `run_summary.json`

To omogućava:
- dalju analizu van aplikacije
- arhiviranje rezultata
- poređenje run-ova
- slanje izvještaja drugim ljudima

---

# 7. Objašnjenje glavnih score dimenzija jednostavnim jezikom

## Catalog Score
Odgovara na pitanje:

> Koliko je proizvodna stranica osnovno kompletna i sadržajno popunjena u HTML-u?

## Machine Score
Odgovara na pitanje:

> Koliko je stranica mašinski čitljiva i koliko su product podaci jasno označeni kroz structured data?

## Commerce Score
Odgovara na pitanje:

> Da li stranica ima osnovne buyer signale potrebne za odluku i praktičnu kupovnu jasnoću?

## Overall Score
Odgovara na pitanju:

> Koliko je stranica ukupno dobra kao početni audit signal, uzimajući u obzir više dimenzija?

---

# 8. Kako tumačiti rezultate

Rezultate ne treba čitati kao apsolutnu presudu.

Pravilno čitanje je:

- score = signal
- flag = upozorenje
- shortlist = prioritet za ručni pregled

Pogrešno čitanje bi bilo:
- “sve iznad 80 je savršeno”
- “sve ispod 40 je sigurno loše”
- “alat je već završio audit”

To nije tačno.

Alat je pomoć pri auditu, ne završni auditor.

---

# 9. Najčešći korisni scenariji upotrebe

Aplikacija je najkorisnija kada želiš:

## 1. Brz pregled većeg broja product stranica
Umjesto ručnog otvaranja desetina ili stotina URL-ova.

## 2. Početnu procjenu kvaliteta webshop kataloga
Posebno:
- HTML kompletnost
- structured data prisutnost
- osnovni buyer signali

## 3. Pronalazak problematičnih proizvoda
Na primjer:
- nema cijene
- nema schema
- nema dovoljno sadržaja
- sumnjiva canonical logika

## 4. Pripremu shortlist-a za ručni review
Što je jedna od najvrjednijih funkcija.

## 5. Interni tehnički i sadržajni pre-audit
Prije dubljeg audita ili većih preporuka za webshop

---

# 10. Poznata ograničenja aplikacije

Vrlo važno: aplikacija ima jasna ograničenja.

## 1. JS-rendered shopovi
Ako je shop jako oslonjen na JavaScript rendering:
- alat može dobiti prazan ili nepotpun HTML
- dio signala može faliti
- rezultati mogu biti slabiji nego što stranica realno jeste

**Kako prepoznati u rezultatima:**

Ako stranica ima JS rendering problem, u tabeli Results taba pojavit
će se kolona `flag_js_rendered = True`. Takvi redovi imaju
napomenu u `indexability_flags` koloni.

Za takve redove, score vrijednosti i missing fields upozorenja su
nepouzdana jer se baziraju na praznom ili minimalnom HTML-u, a ne na
stvarnom sadrzaju koji korisnik vidi u browseru.

Preporuka: stranice sa `flag_js_rendered = True` treba otvoriti
ručno i vizuelno provjeriti prije nego se donese zaključak o
njihovoj kvaliteti.

## 2. Varijante proizvoda
Varijante se mogu pojavljivati kao odvojeni redovi.
Nema nužno savršeno dedupliciranje po SKU logici.

## 3. Price extraction nije savršen
Cijena može biti:
- promašena
- pogrešno pronađena
- višeznačna kod sale/regular/variant prikaza

## 4. Score nije objektivna istina
To je heuristički model.

## 5. Review notes i statusi se pamte između sesija
U Review Queue tabu, sve note i review statusi koje korisnik unese
čuvaju se u fajlu `review_notes.json` unutar output direktorija tog runa:

```
outputs/20240330_143000/review_notes.json
```

To znači da:
- zatvaranje i ponovno otvaranje aplikacije ne briše note
- svaki run ima vlastiti `review_notes.json`
- fajl se može arhivirati zajedno sa CSV rezultatima
- note se mogu pregledati i van aplikacije kao običan JSON

Status vrijednosti koje se čuvaju:
- `pending` — nije pregledano (default)
- `needs_fix` — pregledano, treba popravka
- `reviewed` — pregledano, uredu
- `fixed` — popravka urađena

## 6. GUI nije zamjena za CSV analizu
GUI pomaže, ali kod većih run-ova će CSV i dalje biti važan za dublji pregled.

---

# 11. Kako aplikaciju treba koristiti ispravno

Najzdraviji način korištenja je:

## Korak 1
Pokreni skeniranje na ograničenom uzorku ili prioritetnim URL-ovima.

## Korak 2
Pregledaj Results tab i filtere.

## Korak 3
Pogledaj Review Queue.

## Korak 4
Otvori nekoliko stvarnih stranica iz shortlist-a i provjeri signal.

## Korak 5
Koristi exported CSV/JSON fajlove za dalju obradu.

Dakle:
- prvo automatika
- onda ručna provjera
- onda zaključak

Ne obrnuto.

---

# 12. Kratki sažetak rada aplikacije

Ako sve svedemo na najjednostavniju verziju:

> Aplikacija uzme listu product URL-ova, skine stranice, izvuče HTML i schema signale, izračuna početne score vrijednosti, označi sumnjive slučajeve i pripremi proizvode za ručni audit.

---

# 13. Konačna svrha aplikacije

Konačna svrha aplikacije nije da “presudi” webshopu.

Nego da:

- ubrza početni audit
- smanji ručni posao
- istakne problematične stranice
- pomogne u prioritizaciji
- i da pregledniji ulaz za ozbiljniji ručni review

---

# 14. Završna napomena

Ovu aplikaciju treba posmatrati kao:

- audit pomoćnika
- signal generator
- shortlist alat
- i bazu za dalji razvoj

Ne kao gotov “pametni auditor” koji sam rješava sve.

Ako se tako koristi, onda već sada ima vrlo realnu vrijednost.
