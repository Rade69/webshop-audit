# Tehnička dokumentacija aplikacije — webshop audit alat

## Svrha dokumenta

Ovaj dokument opisuje tehničku arhitekturu aplikacije za početni audit web shopa.

Namijenjen je prvenstveno:
- developeru koji radi na projektu
- AI agentu koji nastavlja razvoj
- osobi koja treba brzo razumjeti strukturu sistema
- budućem refaktoringu i proširenju aplikacije

Dokument ne opisuje samo “šta postoji”, nego i:
- zašto je arhitektura postavljena tako
- gdje su granice odgovornosti
- kako teče obrada podataka
- gdje su poznata ograničenja
- kako aplikaciju dalje širiti bez narušavanja sistema

---

# 1. Osnovna ideja sistema

Aplikacija je alat za **početni audit product stranica web shopa**.

Arhitekturni princip je:
- jasan linearni pipeline
- modularna podjela odgovornosti
- heuristički scoring
- odvajanje backend obrade od GUI sloja
- eksport rezultata za dalju obradu

Aplikacija nije zamišljena kao monolitni “smart auditor”, nego kao sistem koji radi:

> data collection → signal extraction → scoring → prioritization → review support

---

# 2. Arhitekturni model

## 2.1. Linearni backend pipeline

Osnovni tok obrade je:

```text
URL kolekcija → Fetch → Parse HTML → Extract schema → Score → Shortlist → Export
```

To je centralna logika sistema i ne treba je razbijati bez dobrog razloga.

Ovaj tok znači:

1. URL-ovi se prikupljaju
2. stranice se preuzimaju
3. iz HTML-a se izvlače signali
4. iz structured data se izvlače schema podaci
5. kombinuje se jedinstveni zapis po URL-u
6. računa se score i flagovi
7. formira se shortlist
8. rezultati se izvoze

---

## 2.2. Odvajanje GUI sloja

GUI ne smije postati drugi backend.

Preporučeni model je lagani **3-layer pristup**:

### View layer
- prozori
- tabovi
- tabele
- detaljni paneli
- filteri
- dugmad

### Controller / Application layer
- orkestrira GUI akcije
- pokreće backend procese
- učitava rezultate
- vodi stanje run-a
- priprema prikaz podataka

### Domain / Service layer
- postojeći audit backend moduli
- fetch, parsing, schema, scoring, shortlist i export

To znači:
- GUI prikazuje
- kontroler upravlja tokovima iz GUI-ja
- backend moduli rade stvarni posao

---

# 3. Struktura projekta

Predložena / postojeća logika projekta izgleda ovako:

```text
webshop_audit/
├── main.py
├── config.py
├── requirements.txt
├── README.md
│
├── audit/
│   ├── __init__.py
│   ├── sitemap.py
│   ├── fetcher.py
│   ├── async_fetcher.py
│   ├── parser.py
│   ├── schema_parser.py
│   ├── extractor.py
│   ├── scorer.py
│   ├── shortlist.py
│   ├── exporters.py
│   ├── utils.py
│   └── validator.py   # ako postoji i ako se koristi
│
├── gui/
│   ├── main_window.py
│   ├── tabs/
│   │   ├── input_tab.py
│   │   ├── run_tab.py
│   │   ├── results_tab.py
│   │   └── review_queue_tab.py
│   ├── controllers/
│   │   ├── audit_run_controller.py
│   │   ├── results_controller.py
│   │   └── review_controller.py
│   ├── viewmodels/
│   │   ├── run_state.py
│   │   ├── results_state.py
│   │   └── review_state.py
│   ├── widgets/
│   │   ├── filter_bar.py
│   │   ├── product_details_panel.py
│   │   ├── score_badge.py
│   │   └── delegates.py
│   └── styles/
│       ├── __init__.py
│       └── theme.py
│
├── inputs/
├── outputs/
└── tests/
```

---

# 4. Uloge ključnih backend modula

---

## 4.1. `sitemap.py`

### Odgovornost
- pronalazak sitemap URL-ova
- preuzimanje sitemap XML sadržaja
- parsanje URL-ova
- prolazak kroz sitemap index strukture
- osnovna heuristika za izdvajanje vjerovatnih product URL-ova

### Ne smije raditi
- fetch HTML stranica
- scoring
- GUI logiku
- eksport

### Tipičan output
- lista URL-ova
- eventualno signal da je korišten fallback

---

## 4.2. `fetcher.py`

### Odgovornost
- HTTP preuzimanje stranica
- response metadata
- timeout / retry
- redirect handling
- module-level session reuse

### Ključna odluka
`requests.Session()` mora biti na module nivou, ne kreiran po requestu.

### Ne smije raditi
- HTML parsing
- schema parsing
- scoring
- shortlist logiku

### Tipičan output
dict sa:
- original URL
- final URL
- status code
- html
- headers
- error
- response time

---

## 4.3. `async_fetcher.py`

### Odgovornost
- async varijanta fetch sloja
- alternativni način preuzimanja
- potencijalno bolja brzina za veće run-ove

### Napomena
Ovaj modul je dodatni sloj, ali ne smije postati izgovor za komplikovanje ostatka sistema.

Prvo mora biti stabilan sync fetch path.

---

## 4.4. `parser.py`

### Odgovornost
- ekstrakcija signala iz HTML-a
- rad nad već kreiranim `soup` objektom
- title, H1, meta, canonical, robots, price signal, image count, shipping signal, returns signal, itd.

### Ključna odluka
`parser.py` ne smije mutirati glavni `soup`.

Drugim riječima:
- ne koristiti `decompose()` nad glavnim soup objektom ako to mijenja stanje za druge funkcije
- parser funkcije treba da budu “read-only”

### Ne smije raditi
- fetch
- schema parsing
- scoring
- export

---

## 4.5. `schema_parser.py`

### Odgovornost
- JSON-LD parsing
- `@graph` flattening
- pronalazak `Product` i `Offer` objekata
- normalizacija schema polja

### Tipična polja
- schema_product_present
- schema_offer_present
- schema_name
- schema_description
- schema_sku
- schema_gtin
- schema_brand
- schema_price
- schema_currency
- schema_availability

### Ne smije raditi
- HTML parsing
- scoring
- GUI interpretaciju

---

## 4.6. `extractor.py`

### Odgovornost
- kombinuje HTML parsing i schema parsing
- formira standardizovan zapis po URL-u
- definiše centralni data kontrakt sistema

### Ključna odluka
`ProductAuditRow` je centralni kontrakt.

To znači:
- sve kasnije faze se oslanjaju na ovaj oblik podataka
- nova polja treba dodavati pažljivo
- ne treba svaka nova ideja odmah postati polje

### Važnost ovog modula
Ovo je mjesto gdje se razni signali prvi put pretvaraju u jedno objedinjeno stanje po stranici.

---

## 4.7. `scorer.py`

### Odgovornost
- rule-based scoring
- flag detection
- missing field detection
- heurističko rangiranje

### Ključne score dimenzije
- `catalog_score`
- `machine_score`
- `commerce_score`

### Overall model
Ukupan score je kombinacija više dimenzija.

Važno:
- scoring nije istina
- scoring je heuristički signal

### Ne smije raditi
- fetch
- parse HTML
- parse schema
- GUI formatiranje

---

## 4.8. `shortlist.py`

### Odgovornost
- formiranje liste prioritetnih proizvoda za ručni pregled
- korištenje score-a i flagova za selekciju
- po potrebi izdvajanje najboljih uzoraka za poređenje

### Važno
Shortlist nije isto što i score.

Nekad proizvod može imati:
- srednji score
- ali kritičan konkretan problem

i svejedno treba ući u review queue.

---

## 4.9. `exporters.py`

### Odgovornost
- snimanje CSV izlaza
- snimanje JSON summary-ja
- snimanje error logova
- priprema output fajlova po run-u

### Tipični output fajlovi
- `products_raw.csv`
- `products_scored.csv`
- `manual_review_candidates.csv`
- `best_products_sample.csv`
- `non_product_pages.csv`
- `category_summary.csv`
- `errors.csv`
- `run_summary.json`

---

## 4.10. `utils.py`

### Odgovornost
- pomoćne funkcije
- normalizacija
- sigurni helper-i
- URL poređenje
- `is_noindex()` i slične funkcije

### Važno
Ovdje ne treba trpati ozbiljnu poslovnu logiku samo zato što “stane u helper”.

Ako neka logika postane ključna, treba joj dati jasan modul.

---

## 4.11. `validator.py`

### Status
Ako postoji, mora imati jasnu ulogu.

Ako je samo polu-integrisan:
- ili ga treba stvarno uključiti u pipeline
- ili ga treba ukloniti

Polumrtav modul samo stvara lažan osjećaj arhitekturne uređenosti.

---

# 5. Ključne arhitekturne odluke

---

## 5.1. Jedan `soup` objekat po stranici
`extractor.py` kreira i prosljeđuje jedan `soup` parser funkcijama.

Zašto:
- efikasnije
- konzistentnije
- manje dupliranja
- manje rizika od različitih interpretacija istog HTML-a

---

## 5.2. `ProductAuditRow` kao centralni kontrakt
To je najvažniji interni data model.

Zašto:
- omogućava stabilnu komunikaciju između faza
- olakšava DataFrame konverziju
- olakšava export
- smanjuje haos oko “koje polje odakle dolazi”

---

## 5.3. Stroga separacija slojeva
Ne miješati:
- HTML parsing
- schema parsing
- scoring
- shortlist
- GUI prikaz

Ako to krene da se miješa, alat brzo postaje težak za održavanje.

---

## 5.4. Nema circular importa
To je važno jer circular import u modularnim alatima vrlo brzo postane simptom loše arhitekture.

Ako dva modula moraju znati previše jedan o drugom:
- vjerovatno granica odgovornosti nije dobro postavljena

---

## 5.5. GUI kao tanak sloj
GUI ne smije postati mjesto gdje se “ponovo radi backend”.

Na primjer, GUI ne smije:
- sam računati scoring
- raditi canonical poređenje
- sam odlučivati da li je nešto noindex
- parsirati HTML mimo backend-a

GUI treba prikazivati i orkestrirati, ne tumačiti raw web.

---

# 6. Tok podataka kroz sistem

---

## Faza 1 — Input
Ulaz u sistem može biti:
- sitemap URL
- domen
- ručna lista URL-ova
- fajl sa URL-ovima

Rezultat:
- lista ciljanih URL-ova

---

## Faza 2 — Fetch
Za svaki URL se dobija:
- response metadata
- html
- ili error zapis

Rezultat:
- fetch rezultat po URL-u

---

## Faza 3 — Parse HTML
Iz HTML-a se izvlače osnovni signali.

Rezultat:
- HTML signalni skup

---

## Faza 4 — Extract schema
Iz JSON-LD se izvlače mašinski podaci.

Rezultat:
- schema signalni skup

---

## Faza 5 — Unified row
HTML i schema signali se kombinuju.

Rezultat:
- jedan `ProductAuditRow`

---

## Faza 6 — DataFrame
Više `ProductAuditRow` zapisa se pretvara u tablični oblik.

Rezultat:
- raw dataframe

---

## Faza 7 — Scoring i flagovi
Dodaju se:
- score kolone
- missing fields
- indexability flags
- suspicious signali

Rezultat:
- scored dataframe

---

## Faza 8 — Shortlist
Izdvajaju se kandidati za ručni review.

Rezultat:
- review dataframe / queue

---

## Faza 9 — Export
Rezultati se snimaju u izlazne fajlove.

---

## Faza 10 — GUI prikaz
GUI prikazuje:
- progress
- rezultate
- detalje
- review queue
- status i note

---

# 7. Logika score dimenzija

---

## 7.1. Catalog Score
Mjeri HTML kompletnost i osnovnu sadržajnu prisutnost.

Tipični ulazi:
- title
- H1
- meta description
- breadcrumb
- html price signal
- visible text
- image count

Ne treba miješati schema signale u ovu dimenziju.

---

## 7.2. Machine Score
Mjeri structured data i mašinsku čitljivost.

Tipični ulazi:
- Product schema
- Offer schema
- schema price
- schema currency
- schema availability
- schema SKU
- schema brand
- schema GTIN
- canonical signal

Ne treba miješati HTML signale u ovu dimenziju.

---

## 7.3. Commerce Score
Mjeri osnovnu buyer korisnost i komercijalnu jasnoću.

Tipični ulazi:
- price prisutnost
- image count
- shipping signal
- returns signal

---

## 7.4. Overall Score
Kombinacija više dimenzija u jednu ukupnu ocjenu.

Važno:
- nije naučna istina
- nije “objektivni kvalitet”
- nego signal za sortiranje i filtriranje

---

# 8. GUI arhitektura

---

## 8.1. Input tab
Služi za:
- unos izvora URL-ova
- pripremu run-a
- pregled input stanja

---

## 8.2. Run tab
Služi za:
- status rada
- progress
- greške
- log

---

## 8.3. Results tab
Služi za:
- pregled svih rezultata
- filtriranje
- pregled detalja
- mark for review
- export selected

To je glavni radni tab.

---

## 8.4. Review Queue tab
Služi za:
- ručni pregled kandidata
- reason-based workflow
- status ažuriranje
- note workflow

---

## 8.5. GUI widgets i stil
GUI treba biti:
- svijetao
- informativan
- radno udoban
- sa jasnim table fokusom

Zato ima smisla imati:
- centralni theme modul
- score delegate / badge
- status delegate
- flag delegate

---

# 9. Poznata ograničenja sistema

---

## 9.1. JS-heavy shopovi
Bez Playwright ili sličnog render sloja, dio shopova neće vratiti koristan HTML.

---

## 9.2. Varijante
Varijante mogu završiti kao odvojeni redovi i nema savršene deduplikacije.

---

## 9.3. Price extraction
Cijena nije uvijek trivijalna:
- regular vs sale
- variant price
- više brojki na stranici
- frontend state podaci

---

## 9.4. Product detection
URL heuristika i product-page heuristika nisu savršene.

---

## 9.5. Scoring
Heuristički je i treba ga čitati kao signal.

---

# 10. Najzdraviji pravci daljeg razvoja

---

## 10.1. Ojačati product detection
Ne oslanjati se samo na URL pattern.
Dodati bolji post-fetch signal da li je stranica zaista proizvod.

---

## 10.2. Ojačati canonical normalizaciju
Ujednačiti:
- relative canonical
- scheme
- www
- tracking parametre

---

## 10.3. Ojačati price extraction
Dodati slojeve:
- schema price
- HTML explicit price
- oprezni fallback

---

## 10.4. Dodati real integration smoke testove
Ne samo statičke module testove, nego i fixture scenarije koji glume različite tipove shopova.

---

## 10.5. Održati GUI tankim
Bez seljenja backend logike u tabove.

---

## 10.6. Dodati render sloj tek kad ima smisla
Playwright ili sličan alat treba dodati kasnije, ali kao novi sloj, ne kao haotičnu promjenu cijelog sistema.

---

# 11. Tehnički zaključak

Arhitektura aplikacije ima smisla ako se nastavi disciplinovano.

Najveće vrijednosti trenutne strukture su:
- modularnost
- linearan pipeline
- centralni data kontrakt
- jasan export model
- prirodan put ka GUI nadogradnji

Najveći rizici su:
- previše heurističkog samopouzdanja
- miješanje slojeva pri daljem razvoju
- prerano širenje funkcionalnosti bez stabilizacije osnova

---

# 12. Konačna preporuka

Ako se aplikacija dalje razvija, treba se držati ovog principa:

> prvo učvrstiti osnovni pipeline i granice modula, pa tek onda širiti funkcionalnost i UX.

To znači:
- ne praviti rewrite bez razloga
- ne miješati GUI i backend
- ne uvoditi novu kompleksnost prije stabilizacije
- svako proširenje uvoditi kao novi, jasno odvojen sloj

---

# Završna napomena

Ovaj sistem ima dobru osnovu da postane ozbiljan alat, ali samo ako se razvija uz disciplinu.

Drugim riječima:

- modularno
- jasno
- bez prečica
- bez dupliranja logike
- bez miješanja odgovornosti

Ako se toga držiš, alat može rasti bez da se pretvori u haotičan monolit.
