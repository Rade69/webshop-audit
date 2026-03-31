**WebshopAudit — Uputstvo za korištenje**  
WebshopAudit je desktop alat za analizu kvaliteta produktnih stranica na webshopovima.  
   
 Ocjenjuje da li su stranice optimizovane za kataloge, pretraživače i AI agente (structured data, cijena, opis, slike).  
![](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAnEAAAACCAYAAAA3pIp+AAAABmJLR0QA/wD/AP+gvaeTAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAANklEQVR4nO3OQQmAABRAsSeYxZw/lieLGMACBrCCNxG2BFtmZquOAAD4i3Ot7mr/egIAwGvXA6fGBdgoVMwYAAAAAElFTkSuQmCC)  
**Pokretanje aplikacije**  
python main_gui.py  
   
![](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAnEAAAACCAYAAAA3pIp+AAAABmJLR0QA/wD/AP+gvaeTAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAANUlEQVR4nO3OMQ2AABAAsSPBCUbfEm6YmFDBhAU2QtIq6DIzW7UHAMBfnGt1V8fXEwAAXrse/w8F7pbTa1oAAAAASUVORK5CYII=)  
**Tab 1 — Unos**  
Ovdje konfigurirate šta će se skenirati i kako.  
**Unos sitemap-a**  
Najbrži način za učitavanje URL-ova webshopa.  
1. U polje **Sitemap URL** unesite direktan link na sitemap, npr.:  
2. https://www.sportvision.ba/files/sitemap/BIH_ba/sitemap.xml  
   
3. Ili unesite samo domen u polje **Domen** i kliknite  **Auto-otkrivanje** — aplikacija će sama pronaći sitemap iz robots.txt.  
4. Kliknite **Učitaj sitemap**.  
5. Aplikacija preuzima sitemap, filtrira product-like URL-ove i prikazuje broj učitanih URL-ova u statusnom redu (npr. *Učitano 14003 URL-ova*).  
***URL patterne*** * — Opcionalno. Ako webshop koristi nestandardne URL-ove, unesite vlastite fragmente odvojene zarezom, npr. * */jakna/, /patike/, /majica/* *. Ostavite prazno za automatski filter.*  
**Lista URL-ova (alternativa)**  
Kliknite tab **Lista URL-ova** i:  
- Učitajte .txt ili .csv fajl sa URL-ovima (jedan URL po redu), ili  
- Ručno unesite URL-ove u tekstualno polje.  
**Opcije pokretanja**  
| | |  
|-|-|  
| **Opcija** | **Opis** |   
| **Max URL-ova** | Koliko URL-ova će biti skeniran. Preporučeno: 50 za brz test, 200+ za detaljnu analizu. |   
| **Pauza** | Kašnjenje između zahtjeva u sekundama (politeness prema serveru). |   
| **Radni procesi** | Broj paralelnih HTTP zahtjeva. Default 8 je optimalan za većinu shopova. |   
| **Koristi Playwright** | Uključi samo ako shop koristi JavaScript rendering (SPA). Znatno sporije. |   
| **Izlazni dir** | Folder gdje se čuvaju CSV i JSON rezultati. |   
   
**Napredne postavke**  
Težine ocjena određuju kako se računa ukupna ocjena:  
- **Težina kataloga** — kvalitet naslova, opisa, slika (katalog/PIM podaci)  
- **Težina mašine** — Schema.org structured data (JSON-LD), meta tagovi  
- **Težina commerce** — cijena, valuta, dostupnost, SKU, GTIN  
- **Prag agent-ready** — minimalna ocjena da se stranica smatra AI-ready (default 65)  
Sva tri zbrajaju se i normalizuju na 100%.  
![](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAnEAAAACCAYAAAA3pIp+AAAABmJLR0QA/wD/AP+gvaeTAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAANElEQVR4nO3OQQmAABRAsSdYxKY/jMFMIZ7ECt5E2BJsmZmt2gMA4C+Otbqr8+sJAACvXQ85QgYXd/O+eQAAAABJRU5ErkJggg==)  
**Pokretanje skeniranja**  
Kliknite **Pokreni skeniranje** (dugme u donjem desnom uglu taba Unos).  
Aplikacija automatski prelazi na tab **Pokretanje**.  
![](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAnEAAAACCAYAAAA3pIp+AAAABmJLR0QA/wD/AP+gvaeTAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAANUlEQVR4nO3OMQ2AUBBAsUfyRTCh9VRgEBGsWGAjJK2CbjNzVGcAAPzFtapV7V9PAAB47X4AEWgEMAY9+pUAAAAASUVORK5CYII=)  
**Tab 2 — Pokretanje**  
Prati tok skeniranja u realnom vremenu.  
- **Progress bar** — prikazuje procenat završenih URL-ova  
- **Faza** — trenutna operacija (Prikupljanje URL-ova → Preuzimanje → Parsiranje → Bodovanje → Kratka lista)  
- **Statistike** — broj obrađenih, grešaka, kandidata  
- **Živi log** — detaljni log svakog koraka  
**Zaustavljanje**  
Kliknite **Zaustavi** u bilo kom trenutku. Aplikacija završava trenutni batch (do 8 URL-ova), zatim obrađuje i čuva sve što je do tada prikupljeno. Rezultati su dostupni i nakon ranog zaustavljanja.  
![](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAnEAAAACCAYAAAA3pIp+AAAABmJLR0QA/wD/AP+gvaeTAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAANklEQVR4nO3OMQ2AABAAsSNBACPq8MH2NpGACyywEZJWQZeZ2aszAAD+4l6rrTq+ngAA8Nr1AL/KBEe6dElaAAAAAElFTkSuQmCC)  
**Tab 3 — Rezultati**  
Tabela svih skeniranih produktnih stranica sa ocjenama.  
**Kolone**  
| | |  
|-|-|  
| **Kolona** | **Opis** |   
| **Naslov** | Naslov stranice (skraćen) |   
| **Katalog** | Ocjena 0–100 za opis, slike, tekst |   
| **Mašina** | Ocjena 0–100 za structured data (Schema.org) |   
| **Commerce** | Ocjena 0–100 za cijenu, SKU, dostupnost |   
| **Ukupno** | Ponderisani prosjek sva tri |   
| **Oznake** | Problemi detektovani automatski |   
   
Boje ocjena: **zelena** ≥ 70,  **narandžasta** 40–69,  **crvena** < 40.  
**Filteri**  
- **Kategorija** — filtriraj po URL kategoriji  
- **Ocjena Min/Max** — opseg ukupne ocjene  
- **Pretraga** — slobodan tekst po URL-u, naslovu, SKU-u ili GTIN-u  
- **Nema sheme / Nema cijene / Noindex / Problem canonical** — brzi filteri za specifične probleme  
- **Samo kratka lista** — prikaži samo top kandidate za reviziju  
- **Prikaži ne-proizvode** — stranice koje nisu prepoznate kao produktne  
**Detalji stranice**  
Kliknite na red u tabeli da vidite detalje desno:  
- **URL, naslov, H1, canonical, robots** direktivy  
- **Shema** — da li postoji Product JSON-LD, ponuda, cijena, valuta, dostupnost, SKU, GTIN, brend  
- **Signali** — HTML cijena, dostava, povrati, broj slika, dužina teksta  
- **Oznake** — konkretni problemi  
**Akcije**  
| | |  
|-|-|  
| **Dugme** | **Opis** |   
| **Otvori stranicu** | Otvara odabranu stranicu u browseru |   
| **Označi za ručnu reviziju** | Prebacuje odabrane u Red za reviziju |   
| **Izvezi odabrano** | Eksportuje odabrane redove u CSV |   
   
![](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAnEAAAACCAYAAAA3pIp+AAAABmJLR0QA/wD/AP+gvaeTAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAANklEQVR4nO3OMQ2AABAAsSNhRAF6EPYDLhGADSywEZJWQZeZ2aszAAD+4l6rrTq+ngAA8Nr1AIWsBDYDm5cLAAAAAElFTkSuQmCC)  
   
   
   
**Tab 4 — Red za reviziju**  
Lista stranica označenih za ručnu inspekciju.  
**Statusni tok**  
Svaka stranica u redu ima status koji možete mijenjati:  
| | |  
|-|-|  
| **Status** | **Značenje** |   
| **Na čekanju** | Nije još pregledano |   
| **Pregledano** | Pregledano, nema akcije |   
| **Treba popravku** | Identificiran problem koji treba popraviti |   
| **Popravljeno** | Problem je riješen |   
   
**Rad s kandidatima**  
1. Odaberite stranicu iz tabele  
2. Pročitajte detalje desno (URL, ocjena, razlozi za reviziju)  
3. Otvorite stranicu u browseru dugmetom **Otvori stranicu**  
4. Dodajte bilješku u polje za bilješke i kliknite **Ažuriraj bilješku**  
5. Promjenite status odgovarajućim dugmetom ili dropdownom  
Dugme **Sljedeći kandidat** automatski prelazi na sljedeću stranicu u redu.  
![](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAnEAAAACCAYAAAA3pIp+AAAABmJLR0QA/wD/AP+gvaeTAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAAM0lEQVR4nO3KsQ0AIRAEsUW6Qij1KvnevhMSYmKQ7GiCGd09k3wBAOAVf+2o4wYAwE1qAdYuAy151mgcAAAAAElFTkSuQmCC)  
**Izlazni fajlovi**  
Nakon skeniranja u izlaznom direktoriju (default outputs/YYYYMMDD_HHMMSS/) nalaze se:  
| | |  
|-|-|  
| **Fajl** | **Sadržaj** |   
| products_scored.csv | Sve stranice sa ocjenama i svim ekstrahovanim podacima |   
| products_raw.csv | Sirovi podaci prije bodovanja |   
| manual_review_candidates.csv | Kratka lista kandidata za ručnu reviziju |   
| best_products_sample.csv | Uzorak stranica sa najboljim ocjenama |   
| category_summary.csv | Sumarni pregled po kategorijama |   
| non_product_pages.csv | Stranice koje nisu produktne |   
| errors.csv | URL-ovi koji nisu mogli biti preuzeti |   
| run_summary.json | Sažetak cijelog runa (statistike, elapsed time) |   
   
![](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAnEAAAACCAYAAAA3pIp+AAAABmJLR0QA/wD/AP+gvaeTAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAANUlEQVR4nO3OQQmAABRAsSd4NIGRTPXNaQBrWMGbCFuCLTOzV2cAAPzFvVZbdXw9AQDgtesBhZQEOYZGgUEAAAAASUVORK5CYII=)  
**Tipičan tok rada**  
1. Unesite sitemap URL webshopa  
 2. Kliknite "Učitaj sitemap" → sačekajte da se URL-ovi učitaju  
 3. Postavite Max URL-ova na 50 (brz test) ili više za detaljan audit  
 4. Kliknite "Pokreni skeniranje"  
 5. Pratite progress u tabu Pokretanje (3–10 minuta za 50 URL-ova)  
 6. Pregledajte rezultate u tabu Rezultati  
 7. Filtrirajte po "Nema sheme" ili "Nema cijene" za prioritetne probleme  
 8. Označite ključne stranice za reviziju  
 9. Radite kroz Red za reviziju, dodajte bilješke i ažurirajte statuse  
 10. Eksportujte rezultate za izvještaj  
   
![](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAnEAAAACCAYAAAA3pIp+AAAABmJLR0QA/wD/AP+gvaeTAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAANUlEQVR4nO3OMQ2AABAAsSPBCj5fFyM6mJHAjAU2QtIq6DIzW7UHAMBfnGt1V8fXEwAAXrsexOEF35f1aEgAAAAASUVORK5CYII=)  
**Savjeti**  
- **Počnite sa 50 URL-ova** — dovoljno za reprezentativan uzorak kvaliteta shopa  
- **Nema sheme = prioritet** — produkti bez Schema.org JSON-LD su nevidljivi AI agentima i imaju slabu SEO strukturu  
- **Commerce ocjena < 60** — najčešće znači da nedostaje cijena ili dostupnost u structured data  
- **Dužina teksta = 0** — stranica koristi JavaScript rendering; pokušajte sa uključenim Playwright opcijom  
