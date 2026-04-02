# PROMPT — Stabilizacija 2: Category inference

Radiš na projektu **WebshopAudit**.

Prije rada obavezno pročitaj:
- `AGENTS_webshop_audit.md`
- `CLAUDE_webshop_audit.md`

Ovo nije nova velika refaktor faza.  
Ovo je **stabilizacioni zadatak #2: category inference**.

Ne radi sample bucket tuning.  
Ne radi end-to-end test strategy overhaul.  
Ne radi config cleanup.  
Ne radi GUI redesign.  
Ne popravljaj report generator lokalnim hackovima ako je pravi problem u domain sloju.

---

# 1. Cilj zadatka

Cilj je da **category summary postane stvarno poslovno koristan**, a ne da se većina ili sve stranice svode na generičku kategoriju tipa:

- `Proizvodi`

Trenutno je sistem tehnički konzistentan, ali analitički slab, jer category inference nije dovoljno dobar da izdvoji realne grupe proizvoda.

Na kraju rada treba da važi:

- category inference se radi u **jednom canonical mjestu**
- `category_summary.csv` daje smislenije kategorije gdje god je to moguće
- report koristi taj rezultat, a ne svoju lokalnu heuristiku
- fallback ka generičkoj kategoriji postoji, ali tek kao posljednja opcija

---

# 2. Najvažnije pravilo

**Category inference ne smije živjeti u report generatoru kao poseban izvor istine.**

Ako je root problem u tome kako se kategorija izvlači, rješenje mora biti u domain sloju, najprirodnije u:
- `audit/scorer.py`
ili
- malom domain helper modulu koji scorer koristi

Report smije samo koristiti rezultat te logike.

---

# 3. Scope — šta tačno radiš

## 3.1. Pregledaj postojeću category logiku

Obavezno pregledaj:
- `audit/scorer.py`
- `audit/report_generator.py`
- `audit/extractor.py`

Po potrebi pregledaj i:
- `audit/parser.py`
- `audit/utils.py`
- postojeći `category_summary.csv`
- sample outpute / stvarne URL-ove

Treba da potvrdiš:
- kako se trenutno izvlači kategorija
- da li se koristi samo `breadcrumb_text`
- šta se desi kad breadcrumb nije koristan
- zašto rezultat završava kao `Proizvodi`

---

## 3.2. Definiši jaču hijerarhiju category inference pravila

Potrebno je napraviti jasnu hijerarhiju pokušaja, npr. ovim redom ili sličnim redom ako nađeš bolji:

1. **breadcrumb_text**
   - koristi najkorisniji segment, ne naslijepo
   - preskoči generičke segmente tipa:
     - Home
     - Početna
     - Proizvodi
     - Shop
     - Katalog
     - Ostalo sličnog tipa

2. **URL pattern**
   - ako URL jasno sugeriše kategoriju, koristi ga
   - npr. `/majica/`, `/dukserica/`, `/patike/`, `/jakna/`

3. **title / h1 signal**
   - ako ni breadcrumb ni URL nisu dovoljni, koristi jasan signal iz naslova ili H1
   - ali samo ako je dovoljno stabilan i nije marketinški šum

4. **fallback**
   - tek na kraju koristi nešto poput `Unknown` ili drugu jasno definisanu rezervnu vrijednost
   - ne koristiti generički `Proizvodi` prerano ako to ne nosi stvarnu informaciju

### Važno
Ne moraš slijepo pratiti baš ovaj redoslijed ako iz koda i stvarnih URL-ova vidiš bolji, ali mora postojati:
- jasan prioritet
- jasan fallback
- jasan razlog zašto će rezultat biti bolji nego prije

---

## 3.3. Uvedi filtriranje generičkih kategorija

Trenutno je jedan od ključnih problema što generički pojmovi gutaju sve.

Potrebno je uvesti logiku koja prepoznaje i izbjegava kategorije koje nisu analitički korisne, npr:
- Proizvodi
- Shop
- Katalog
- Artikli
- Home
- Početna

Ako su svi raspoloživi signali generički, onda je bolje:
- vratiti `Unknown`
ili
- jasno dokumentovan fallback

nego lažno korisnu kategoriju.

---

## 3.4. Održi logiku determinističkom i čitljivom

Ovo nije mjesto za “smart AI inference”.

Potrebno je da logika bude:
- deterministička
- čitljiva
- testabilna
- bazirana na signalima koje već imaš

Nemoj uvoditi:
- komplikovane heuristike koje je teško braniti
- fuzzy magiju bez jasnog razloga
- logiku koja će kasnije biti nemoguća za održavanje

---

## 3.5. Uskladi summary i report sloj

Kad poboljšaš category inference, provjeri:
- `category_summary.csv`
- report sekciju za kategorije

Report treba da koristi bolji rezultat iz domain sloja, bez vlastitog dodatnog “popravljanja” kategorija.

---

## 3.6. Dodaj testove za realne obrasce

Dodaj ili ažuriraj testove tako da štite scenarije kao što su:

- breadcrumb sa generičkim segmentom + koristan dublji segment
- breadcrumb potpuno beskoristan, ali URL jasan
- breadcrumb i URL nejasni, ali H1/title koristan
- svi signali generički → fallback `Unknown`
- više URL-ova različitih tipova daje različite kategorije

Ako je moguće, koristi primjere koji liče na stvarne webshop obrasce, ne samo sintetičke trivialne stringove.

---

# 4. Među-zavisnosti koje moraš obavezno provjeriti

Ako popravljaš category inference, moraš provjeriti uticaj na:

1. **`category_summary.csv`**
   - da sadrži korisnije kategorije
   - da ne ostaje trivijalno generički bez razloga

2. **`audit_report.docx`**
   - da kategorije sekcija koristi novi rezultat
   - da report ne puca ako je neka kategorija `Unknown`

3. **Scorer / summary logika**
   - da se category summary i dalje pravilno agregira
   - da ne uvodiš drugi izvor istine

4. **Output shape**
   - da ne lomiš postojeće report/export očekivanje bez potrebe

5. **Testovi**
   - da nova heuristika bude zaštićena

---

# 5. Šta je dozvoljeno, a šta nije

## Dozvoljeno
- poboljšanje category inference u `scorer.py`
- uvođenje malog helpera ako je to čišće
- lista generičkih kategorija za ignorisanje
- URL/title/H1 fallback pravila
- testovi za category inference i summary

## Nije dozvoljeno
- report-only hack da kategorije izgledaju bolje
- mijenjanje scoring semantike
- sample bucket tuning
- GUI izmjene
- config cleanup van onog što je baš nužno
- “AI” heuristike koje nisu transparentne

---

# 6. Kriterij uspjeha

Zadatak je završen tek kad su ispunjeni svi uslovi:

- category inference živi u jednom canonical mjestu
- generičke kategorije se ne koriste prerano
- `category_summary.csv` daje korisnije grupe gdje god je to moguće
- report koristi taj rezultat bez lokalne paralelne logike
- testovi štite glavne obrasce i fallback slučajeve
- logika ostaje čitljiva i održiva

---

# 7. Testovi

Dodaj ili ažuriraj testove tako da štite:

- breadcrumb-based inference
- URL-based fallback
- title/H1 fallback
- ignorisanje generičkih kategorija
- `Unknown` fallback
- category summary agregaciju za više kategorija

Ako nemaš pun integration test kroz report:
- napiši šta je testirano na domain nivou
- šta treba ručno provjeriti generisanjem stvarnog reporta

---

# 8. Očekivani izlaz od tebe

Vrati odgovor u ovom formatu:

## 1. Šta je bio stvarni uzrok slabog category summary-ja
- kratko i iskreno

## 2. Šta je sada promijenjeno
- kratko i jasno

## 3. Pogođeni fajlovi
- kompletan spisak

## 4. Gdje sada živi category inference logika
- tačno mjesto
- koji signali se koriste
- kojim redoslijedom

## 5. Kako se sada rješavaju generičke kategorije
- šta se ignoriše
- kada se koristi fallback

## 6. Među-zavisnosti provjerene
- `category_summary.csv`
- `audit_report.docx`
- scorer / summary tok
- testovi

## 7. Rizici koji ostaju
- napiši iskreno ako još ima slabih slučajeva

## 8. Testovi
- koje si pokrenuo
- koji su prošli
- šta treba ručno provjeriti

Ako je nešto blokirano, napiši:

**BLOKIRANO**
- razlog
- šta tačno treba razjasniti

---

# 9. Završna napomena

Ovaj zadatak nije “napravi ljepše nazive kategorija”.

Ovo je:
- popravljanje analitičke vrijednosti summary sloja
- uklanjanje lažno korisne generičke kategorizacije
- jačanje jednog od najvažnijih poslovnih prikaza u izvještaju
