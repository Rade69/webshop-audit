# CLAUDE.md — radne instrukcije za AI asistenta na projektu **WebshopAudit**

## ⚠️ JEZIK

**Komunikacija sa korisnikom ide na srpskom / bosanskom / hrvatskom latinica stilu, jasno i precizno.**  
Kod, imena funkcija i postojeći komentari u projektu mogu ostati na engleskom gdje je to već ustaljeno.

---

## 1. Prvo pročitaj projekat, ne nagađaj

Prije bilo kakve izmjene agent mora:

1. Pročitati relevantne fajlove koje dira
2. Provjeriti stvarnu arhitekturu projekta
3. Identifikovati source-of-truth modul za dio koji mijenja
4. Mapirati zavisne fajlove prije izmjene

### Minimalni read set po tipu zadatka

**Ako je zadatak vezan za scoring**
- `audit/extractor.py`
- `audit/scorer.py`
- `audit/shortlist.py`
- relevantne testove

**Ako je zadatak vezan za GUI rezultate**
- `gui/controllers/results_controller.py`
- `gui/tabs/results_tab.py`
- `gui/viewmodels/results_state.py`
- `audit/scorer.py`
- `audit/extractor.py`

**Ako je zadatak vezan za review queue**
- `gui/controllers/review_controller.py`
- `gui/tabs/review_queue_tab.py`
- `gui/viewmodels/review_state.py`
- `audit/shortlist.py`
- CSV/output očekivanja

**Ako je zadatak vezan za izvještaj**
- `audit/report_generator.py`
- `audit/exporters.py`
- `audit/scorer.py`
- stvarne output CSV fajlove ako postoje

---

## 2. Osnovni mentalni model projekta

Ovo nije klasičan crawler, niti samo GUI alat.  
Ovo je **audit engine + pregledni interfejs**.

### Tok podataka

```text
Sitemap / URL source
    ↓
Fetcher
    ↓
Parser + Schema parser
    ↓
Extractor → ProductAuditRow / raw DataFrame
    ↓
Scorer → scored DataFrame + flags + summaries
    ↓
Shortlist / Export / Report
    ↓
GUI prikaz i review workflow
```

Ako popravljaš nešto niže u toku, moraš provjeriti uticaj na sve više slojeve.

---

## 3. Najvažniji rizik projekta

### Data contract drift

Najveći tehnički rizik nije scraping nego **neusklađenost kolona i značenja podataka** između backend i GUI/report sloja.

Zato prije svake izmjene provjeri:
- da li naziv kolone već postoji kao canonical
- da li GUI koristi staro ime
- da li report generator koristi staro ime
- da li testovi očekuju staru semantiku

### Pravilo

**Ne uvoditi lokalne aliase kao “brzo rješenje”.**  
Ako je polje pogrešno imenovano, popravi ga na izvoru i propagiraj odgovorno.

---

## 4. Kada je izmjena dobra, a kada loša

### Dobra izmjena
- smanjuje duplikaciju logike
- pojačava source-of-truth
- razdvaja UI od business logike
- zadržava ili poboljšava testabilnost
- poštuje postojeće data contracte ili ih planski migrira

### Loša izmjena
- popravlja samo jedan tab i razbija report
- uvodi “helper” koji sakriva pogrešnu kolonu
- dodaje feature bez provjere CSV/export posljedica
- računa rezultate u GUI-u umjesto u domain sloju
- oslanja se na pretpostavke umjesto čitanja fajlova

---

## 5. Pravila za GUI rad

### Obavezno
- GUI mora ostati tanak koliko je moguće
- Controller orkestrira, tab prikazuje
- Viewmodel/state drži stanje filtera, selekcije i prikaza
- Stil (`theme.py`) ne smije nositi business logiku

### Posebno pazi na:
- `results_tab.py`
- `input_tab.py`
- `review_queue_tab.py`

To su veliki fajlovi i najlakše je u njih ubaciti “samo još malo logike”.  
To ne radi.

### Ako dodaješ novo dugme / filter
Moraš odgovoriti na pitanja:
1. Koje canonical kolone koristi?
2. Gdje se računa njegovo značenje?
3. Da li isti kriterij postoji već u scorer/shortlist sloju?
4. Da li to treba biti GUI akcija ili domain pravilo?

---

## 6. Pravila za shortlist i review

Review queue treba služiti ljudima, ne zatrpavati ih.

Kad radiš na shortlist logici, moraš razlikovati:
- **kritične stranice**
- **stranice s niskim scoreom**
- **stranice za poređenje / benchmark**
- **ne-produktne stranice**

### Obavezno razmišljanje
Ako gotovo cijeli uzorak završi u `manual_review_candidates.csv`, shortlist nije shortlist.

### Zabrana
Ne tretirati “najnižih N scoreova” kao dovoljno dobar review model bez severity logike.

---

## 7. Pravila za report generator

`audit/report_generator.py` mora čitati **stvarne canonical output kolone**.

### Zabranjeno
- pretpostaviti stara imena kolona
- lokalno prevoditi kolone bez validacije
- proizvoditi lijep report koji je podatkovno netačan

### Obavezno
Ako neka očekivana kolona ne postoji:
- fail loud ili
- eksplicitno fallback + upozorenje

Nikad tihi fallback koji može dati pogrešan izvještaj.

---

## 8. Pravila za config i pragove

Ako mijenjaš:
- score weight
- threshold
- URL pattern
- timeout
- worker count
- shortlist veličinu
- heuristike za content/image/price detection

to mora ići kroz `config.py` ili jasno definisan config sloj.

### Zabrana
Hardkodirati takve vrijednosti u:
- tabovima
- kontrolerima
- report generatoru
- testovima bez razloga

---

## 9. Pravila za testiranje

### Minimum nakon svake ozbiljnije izmjene

- relevantni unit testovi pogođenih modula
- najmanje jedan integration tok ako je pogođena pipeline logika
- provjera output shape-a ako su mijenjane kolone
- GUI testovi ako je mijenjan controller/tab/state

### Kad nemaš okruženje za GUI runtime
Nemoj tvrditi da je GUI “ispravan”.  
Reci tačno:
- šta si provjerio statički
- koji testovi su prošli
- šta ostaje za ručnu provjeru

---

## 10. Kako pisati promjene

Kad isporučuješ rješenje, napiši kratko i precizno:

### Obavezna struktura odgovora
1. Šta je cilj izmjene
2. Koji fajlovi su promijenjeni
3. Koje među-zavisnosti su uzete u obzir
4. Šta je potencijalno rizično
5. Šta treba testirati ručno

### Ako postoji sumnja
Napiši je direktno.  
Ne glumi sigurnost.

---

## 11. Pravila za refaktor po fazama

Ako radiš veći refaktor:

### Faza 1 — Konsolidacija contracta
- extractor/scorer/report/GUI usklađivanje
- uklanjanje zastarjelih aliasa
- testovi za shape podataka

### Faza 2 — Logika shortlist/review
- severity model
- manje zagađenje review queue-a
- jasni reason code-ovi

### Faza 3 — GUI razdvajanje
- tanji tabovi
- više logike u controller/state sloju
- manje direktnog tumačenja DataFrame-a u view-u

### Faza 4 — Kvalitet summary/reporting sloja
- category inference
- sitewide metrics
- dosljedan izvještaj

---

## 12. Stil rada

- Budi kritičan prema postojećem kodu, ali ne destruktivan
- Ne širi obim zadatka bez potrebe
- Ne dodaji “usputne” featuree
- Čuvaj postojeće ponašanje osim ako je eksplicitno pogrešno
- Kad vidiš sistemski problem, reci ga otvoreno

---

## 13. Šta posebno provjeriti u ovom projektu

### Pri svakoj ozbiljnoj izmjeni pregledaj:
- `ProductAuditRow` shape
- score/flag kolone
- `manual_review_candidates.csv` semantiku
- `best_products_sample.csv` semantiku
- `category_summary.csv` semantiku
- Results tab filtere
- Review tab detalje i statuse

### Ako diraš CLI / pipeline
Provjeri da GUI i CLI ne odu različitim putevima.

---

## 14. Poželjni izlaz za agenta

Kad završiš izmjenu, vrati:

```text
URAĐENO:
- ...

POGOĐENI FAJLOVI:
- ...

MEĐU-ZAVISNOSTI PROVJERENE:
- ...

RIZICI:
- ...

TEST / RUČNA PROVJERA:
- ...
```

Ako ne možeš sigurno završiti:

```text
BLOKIRANO:
- ...

POTREBNO RAZJAŠNJENJE:
- ...
```

---

## 15. Suština ovog projekta u jednoj rečenici

**WebshopAudit mora imati jedno stabilno audit jezgro, a GUI i report sloj smiju ga samo prikazivati i koristiti — ne reinterpretirati na svoj način.**

---

*Ovaj fajl je prilagođen projektu WebshopAudit da agenti rade konzistentno, uz svijest o stvarnim među-zavisnostima i trenutnim rizicima projekta.*
