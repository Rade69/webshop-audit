**WebshopAudit — Detaljno korisničko uputstvo za početnike**  
**1. Šta je WebshopAudit i čemu služi**  
**WebshopAudit** je desktop aplikacija za analizu produktnih stranica na webshopovima.  
Njena svrha je da pomogne da se otkrije:  
- da li su produktne stranice tehnički ispravne  
- da li imaju dovoljno kvalitetne podatke za kataloge i pretraživače  
- da li su dovoljno jasne za AI agente i automatizovane shopping sisteme  
- koje stranice treba prvo ručno pregledati i popraviti  
Aplikacija ne služi za prodaju proizvoda, uređivanje webshopa ili direktno popravljanje sadržaja.  
   
 Ona služi da:  
1. skenira odabrane URL-ove  
2. izvuče podatke sa stranica  
3. ocijeni kvalitet tih stranica  
4. napravi listu prioriteta za reviziju  
5. izveze rezultate i izvještaj  
![](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAnEAAAACCAYAAAA3pIp+AAAABmJLR0QA/wD/AP+gvaeTAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAAM0lEQVR4nO3OMQ0AIAwAwZKQ6kBqjSAOJywYYCIkd9OP36pqRMQMAAB+sfqJfLoBAMCN3NYoAzBA+QG0AAAAAElFTkSuQmCC)  
**2. Ko treba koristiti ovu aplikaciju**  
Aplikacija je korisna za:  
- vlasnike webshopova  
- SEO i ecommerce konsultante  
- tehnička lica koja održavaju katalog proizvoda  
- timove koji žele provjeriti spremnost webshopa za AI pretragu i shopping agente  
- developere koji žele brzo provjeriti kvalitet outputa na produktnim stranicama  
Ako prvi put koristiš aplikaciju, ne moraš znati kako kod radi.  
   
 Dovoljno je da razumiješ:  
- šta želiš skenirati  
- kako da pokreneš audit  
- kako da pročitaš rezultate  
- kako da izvučeš prioritete za popravke  
![](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAnEAAAACCAYAAAA3pIp+AAAABmJLR0QA/wD/AP+gvaeTAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAANklEQVR4nO3OMQ2AABAAsSNBACPykMH4NpGACyywEZJWQZeZ2aszAAD+4l6rrTo+jgAA8N71AL/CBEiG5xPoAAAAAElFTkSuQmCC)  
**3. Šta aplikacija zapravo provjerava**  
WebshopAudit na svakoj produktnoj stranici provjerava više grupa signala.  
**3.1. Katalog signali**  
Ovdje gleda:  
- naslov stranice  
- H1 naslov  
- opis  
- količinu vidljivog teksta  
- slike i produktne slike  
- osnovnu “potpunost” produktne stranice  
Ovaj dio odgovara na pitanje:  
**“Da li je stranica dovoljno kompletna kao katalog zapis?”**  
**3.2. Mašinski signali**  
Ovdje gleda:  
- Schema.org / JSON-LD structured data  
- Product schema  
- Offer schema  
- price, availability, SKU, GTIN, brand  
- druge signale koje mašine i pretraživači koriste za razumijevanje stranice  
Ovaj dio odgovara na pitanje:  
**“Da li pretraživači i AI sistemi mogu mašinski razumjeti proizvod?”**  
**3.3. Commerce signali**  
Ovdje gleda:  
- da li postoji cijena  
- da li postoji valuta  
- da li postoji dostupnost  
- da li postoje shipping / returns signali  
- da li produkt ima dovoljno komercijalnih podataka  
   
   
Ovaj dio odgovara na pitanje:  
**“Da li stranica izgleda kao prava kupovna stranica, a ne samo opis proizvoda?”**  
![](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAnEAAAACCAYAAAA3pIp+AAAABmJLR0QA/wD/AP+gvaeTAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAANklEQVR4nO3OQQmAABRAsSfYxZo/jzlMYQLPJrCCNxG2BFtmZquOAAD4i3Ot7mr/egIAwGvXA4q7Bc870TqdAAAAAElFTkSuQmCC)  
**4. Šta ti treba prije prvog korištenja**  
Prije pokretanja aplikacije pripremi sljedeće:  
**Obavezno**  
- domen webshopa koji želiš analizirati  
   
 npr. https://www.sportvision.ba  
**Poželjno**  
- direktan link na sitemap ako ga znaš  
   
 npr. https://example.com/sitemap.xml  
**Alternativa**  
Ako nemaš sitemap, možeš koristiti:  
- ručnu listu URL-ova  
- .txt fajl sa URL-ovima  
- .csv fajl sa URL-ovima  
**Za prvi test preporuka**  
Nemoj odmah skenirati hiljade URL-ova.  
   
 Za prvi run koristi:  
- **10 URL-ova** ako samo testiraš da li sve radi  
- **50 URL-ova** ako želiš prvi smislen audit uzorak  
![](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAnEAAAACCAYAAAA3pIp+AAAABmJLR0QA/wD/AP+gvaeTAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAANUlEQVR4nO3OQQmAABRAsSd4NIGBzPXBmAawhhW8ibAl2DIze3UGAMBf3Gu1VcfXEwAAXrsehaQEN+8fLHEAAAAASUVORK5CYII=)  
   
   
   
**5. Kako pokrenuti aplikaciju**  
Aplikacija se pokreće komandnom linijom.  
Primjer:  
python main_gui.py  
   
Ako je sve u redu, otvoriće se glavni prozor aplikacije sa više tabova.  
Ako se aplikacija ne otvara:  
- provjeri da li si u pravom folderu projekta  
- provjeri da li su zavisnosti instalirane  
- provjeri da li koristiš pravi Python environment  
![](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAnEAAAACCAYAAAA3pIp+AAAABmJLR0QA/wD/AP+gvaeTAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAANUlEQVR4nO3OQQmAABRAsSeYxKS/kJkED6bwYAVvImwJtszMVu0BAPAXx1rd1fn1BACA164HHDwF+DpPyKwAAAAASUVORK5CYII=)  
**6. Pregled glavnog interfejsa**  
Aplikacija je organizovana kroz 4 glavna taba:  
1. **Unos**  
2. **Pokretanje**  
3. **Rezultati**  
4. **Red za reviziju**  
Najjednostavnije je da ih razumiješ ovako:  
- **Unos** = šta želiš skenirati i pod kojim uslovima  
- **Pokretanje** = šta aplikacija trenutno radi  
- **Rezultati** = kompletan pregled svih skeniranih stranica  
- **Red za reviziju** = mali skup stranica koje traže ručnu pažnju  
![](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAnEAAAACCAYAAAA3pIp+AAAABmJLR0QA/wD/AP+gvaeTAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAANElEQVR4nO3OUQmAABBAsSeIWMICprwEpjSIFfwTYUuwZWaO6goAgL+412qrzq8nAAC8tj8tdQNNdXaCdAAAAABJRU5ErkJggg==)  
**7. Prvi rad sa aplikacijom — korak po korak**  
**Korak 1: Otvori tab “Unos”**  
To je početni tab u kojem određuješ:  
- odakle aplikacija uzima URL-ove  
- koliko URL-ova će obraditi  
- koliko agresivno će skenirati  
- gdje će čuvati rezultate  
![](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAnEAAAACCAYAAAA3pIp+AAAABmJLR0QA/wD/AP+gvaeTAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAANklEQVR4nO3OQQmAABRAsScYxpg/h5VMYARvRrCCNxG2BFtmZquOAAD4i3Ot7mr/egIAwGvXA224BcUMk6pDAAAAAElFTkSuQmCC)  
**Korak 2: Izaberi način unosa URL-ova**  
Postoje dva glavna načina.  
**Varijanta A — Sitemap**  
Ovo je najlakši i najbolji način.  
Koristi ga kad:  
- webshop ima sitemap  
- želiš brzo prikupiti puno produktnih URL-ova  
- želiš reprezentativan uzorak  
Možeš uraditi jedno od sljedećeg:  
***Opcija 1 — unesi direktan sitemap URL***  
U polje za sitemap unesi puni sitemap link, npr:  
https://www.sportvision.ba/files/sitemap/BIH_ba/sitemap.xml  
   
***Opcija 2 — unesi samo domen i koristi auto-otkrivanje***  
U polje **Domen** unesi npr:  
https://www.sportvision.ba  
   
Zatim klikni na opciju za auto-otkrivanje sitemap-a.  
Aplikacija će pokušati:  
- da pročita robots.txt  
- da pronađe sitemap  
- da pripremi URL-ove za skeniranje  
**Varijanta B — Lista URL-ova**  
Koristi je kada:  
- nemaš sitemap  
- želiš analizirati tačno određene stranice  
- radiš ciljanu provjeru nekoliko problematičnih URL-ova  
Možeš:  
- učitati .txt fajl  
- učitati .csv fajl  
- ručno nalijepiti URL-ove  
Pravilo:  
- jedan URL po redu  
- koristi pune URL-ove kad god je moguće  
![](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAnEAAAACCAYAAAA3pIp+AAAABmJLR0QA/wD/AP+gvaeTAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAANklEQVR4nO3OMQ2AABAAsSPBCj7fFRYQwYwEZiywEZJWQZeZ2ao9AAD+4lyruzq+ngAA8Nr1AMTJBeJDClAyAAAAAElFTkSuQmCC)  
**Korak 3: Učitaj URL-ove**  
Ako radiš sa sitemapom:  
1. unesi sitemap ili domen  
2. klikni **Učitaj sitemap**  
3. sačekaj da aplikacija:  
- pronađe sitemap  
- učita URL-ove  
- filtrira “product-like” stranice  
4. provjeri status poruku koja kaže koliko je URL-ova učitano  
**Šta znači “product-like URL”**  
To su URL-ovi koji po obrascu liče na produktne stranice, npr:  
- /majica/...  
- /patike/...  
- /jakna/...  
Aplikacija pokušava automatski da odvoji produktne URL-ove od:  
- category stranica  
- homepage  
- landing stranica  
- drugih ne-produktnih sadržaja  
Ako webshop koristi neobične URL-ove, možeš pomoći aplikaciji preko **URL patterna**.  
![](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAnEAAAACCAYAAAA3pIp+AAAABmJLR0QA/wD/AP+gvaeTAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAANUlEQVR4nO3OMQ2AABAAsSNhZscYahheJwqQgQU2QtIq6DIze3UGAMBf3Gu1VcfXEwAAXrseoqcEQXyAWBgAAAAASUVORK5CYII=)  
   
**Korak 4: Po potrebi unesi URL patterne**  
Ovo je naprednija opcija.  
Koristi je samo ako:  
- znaš da webshop nema standardne produktne URL-ove  
- vidiš da aplikacija učitava premalo relevantnih URL-ova  
- želiš pomoći filtriranju  
Primjeri patterna:  
/jakna/, /patike/, /majica/, /bra/, /dukserica/  
   
Ako nisi siguran, ostavi prazno.  
   
 Za većinu prvih testova to nije potrebno.  
![](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAnEAAAACCAYAAAA3pIp+AAAABmJLR0QA/wD/AP+gvaeTAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAANUlEQVR4nO3OMQ2AABAAsSNBCUrfDqrYGVDAgAU2QtIq6DIzW7UHAMBfHGt1V+fXEwAAXrseHCQGBEuErVgAAAAASUVORK5CYII=)  
**Korak 5: Postavi osnovne parametre skeniranja**  
Najvažnija polja su:  
**Max URL-ova**  
Određuje koliko URL-ova će se stvarno skenirati.  
Preporuka:  
- **10** za prvi tehnički test  
- **50** za prvi ozbiljan pregled  
- **200+** za ozbiljniji audit  
Nemoj odmah koristiti ogroman broj ako prvi put radiš s aplikacijom.  
**Pauza**  
To je kašnjenje između zahtjeva prema serveru.  
Veća pauza znači:  
- sporije skeniranje  
- manji pritisak na webshop server  
Tipične vrijednosti:  
- 0.5 sekundi = razumno za većinu slučajeva  
- 1.0 sekunda = konzervativnije  
- veće vrijednosti = sporije, ali pažljivije  
**Radni procesi / workers**  
Broj paralelnih zahtjeva.  
Tipičan default:  
- 8  
Za prvi test to je obično sasvim u redu.  
**Koristi Playwright**  
Uključi samo ako sumnjaš da webshop:  
- prikazuje sadržaj preko JavaScript-a  
- ne pokazuje cijene/tekst/slike u običnom HTML-u  
- izgleda “prazno” u rezultatima iako u browseru sve vidiš  
Važno:  
- Playwright je sporiji  
- ne koristi ga bez potrebe  
**Izlazni direktorij**  
Mjesto gdje će rezultati biti sačuvani.  
Ako ne znaš šta da staviš, koristi podrazumijevani izlazni folder.  
![](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAnEAAAACCAYAAAA3pIp+AAAABmJLR0QA/wD/AP+gvaeTAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAANUlEQVR4nO3OQQmAABRAsSd40A5GMORPYEt7WMGbCFuCLTNzVFcAAPzFvVZbdX49AQDgtf0BSrIDUgOg4eAAAAAASUVORK5CYII=)  
**Korak 6: Napredne postavke**  
Ovdje podešavaš kako se računa ukupna ocjena.  
**Težina kataloga**  
Koliko utiču:  
- naslov  
- opis  
- slike  
- tekst  
**Težina mašine**  
Koliko utiču:  
- structured data  
- schema signali  
- mašinska razumljivost  
**Težina commerce**  
Koliko utiču:  
- cijena  
- valuta  
- dostupnost  
- SKU / GTIN  
**Prag agent-ready**  
Minimalna ukupna ocjena da bi stranica bila smatrana dovoljno dobrom za AI-ready status.  
Ako si početnik:  
- ostavi default vrijednosti  
Te postavke mijenjaj tek kad već znaš kako želiš da interpretiraš audit.  
![](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAnEAAAACCAYAAAA3pIp+AAAABmJLR0QA/wD/AP+gvaeTAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAANUlEQVR4nO3OMQ2AUBBAsUfyRTCh9VRgEBGsWGAjJK2CbjNzVGcAAPzFtapV7V9PAAB47X4AEWgEMAY9+pUAAAAASUVORK5CYII=)  
**Korak 7: Pokreni skeniranje**  
Klikni **Pokreni skeniranje**.  
Nakon toga aplikacija automatski prelazi na tab **Pokretanje**.  
![](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAnEAAAACCAYAAAA3pIp+AAAABmJLR0QA/wD/AP+gvaeTAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAANUlEQVR4nO3OMQ2AABAAsSNhwgJOUPcjIpnRgQU2QtIq6DIze3UGAMBf3Gu1VcfXEwAAXrseaJEEL8XMiYMAAAAASUVORK5CYII=)  
**8. Tab “Pokretanje” — šta gledaš dok audit radi**  
Ovaj tab prikazuje tok rada u realnom vremenu.  
**Šta se normalno dešava**  
Audit obično ide kroz ove faze:  
1. **Prikupljanje URL-ova**  
2. **Preuzimanje stranica**  
3. **Parsiranje**  
4. **Bodovanje**  
5. **Kratka lista**  
6. **Eksport rezultata**  
7. **Izvještaj** (ako je uključen)  
**Elementi koje vidiš**  
**Progress bar**  
Pokazuje koliko je posla završeno.  
**Faza**  
Pokazuje trenutni korak procesa.  
**Statistike**  
Obično vidiš:  
- koliko URL-ova je obrađeno  
- koliko ima grešaka  
- koliko ima kandidata za reviziju  
**Živi log**  
Tu vidiš detaljnije poruke:  
- šta je učitano  
- šta je eksportovano  
- da li je došlo do greške  
- koje output fajlove je aplikacija napravila  
![](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAnEAAAACCAYAAAA3pIp+AAAABmJLR0QA/wD/AP+gvaeTAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAANklEQVR4nO3OMQ2AABAAsSNhYMEBIpD4ArCJDyywEZJWQZeZOaorAAD+4l6rrTq/ngAA8Nr+AEqmA1hl45m5AAAAAElFTkSuQmCC)  
**Ako želiš zaustaviti audit**  
Klikni **Zaustavi**.  
Aplikacija neće “zaboraviti sve”, nego će pokušati da:  
- završi trenutni mali batch  
- sačuva ono što je do tada obradila  
- napravi djelimične rezultate  
To znači da i prekinut run često može biti koristan.  
![](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAnEAAAACCAYAAAA3pIp+AAAABmJLR0QA/wD/AP+gvaeTAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAANklEQVR4nO3OQQmAABRAsScYxpg/i2XMYARvRrCCNxG2BFtmZquOAAD4i3Ot7mr/egIAwGvXA22YBcnkstSpAAAAAElFTkSuQmCC)  
**9. Tab “Rezultati” — kako se čita**  
Ovdje se vidi tabela svih obrađenih produktnih stranica.  
**Šta tabela predstavlja**  
Svaki red je jedna analizirana stranica.  
Kolone obično uključuju:  
- naslov  
- katalog score  
- mašina score  
- commerce score  
- ukupna ocjena  
- oznake / problemi  
![](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAnEAAAACCAYAAAA3pIp+AAAABmJLR0QA/wD/AP+gvaeTAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAANElEQVR4nO3OQQmAABRAsSdYxKY/jMFMIZ7ECt5E2BJsmZmt2gMA4C+Otbqr8+sJAACvXQ85QgYXd/O+eQAAAABJRU5ErkJggg==)  
**Kako čitati ocjene**  
**Katalog**  
Visok rezultat znači da stranica ima:  
- naslov  
- slike  
- tekst  
- dovoljno osnovnog sadržaja  
**Mašina**  
Visok rezultat znači da stranica ima:  
- structured data  
- Product schema  
- Offer schema  
- semantički korisne signale  
**Commerce**  
Visok rezultat znači da stranica ima:  
- cijenu  
- dostupnost  
- SKU / GTIN  
- jasan kupovni kontekst  
**Ukupno**  
To je ponderisani zbir prethodnih grupa.  
![](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAnEAAAACCAYAAAA3pIp+AAAABmJLR0QA/wD/AP+gvaeTAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAANUlEQVR4nO3OMQ2AABAAsSPBCj5fFyM6mJHAjAU2QtIq6DIzW7UHAMBfnGt1V8fXEwAAXrsexOEF35f1aEgAAAAASUVORK5CYII=)  
**Boje ocjena**  
Obično važi:  
- **zelena** = dobro  
- **narandžasta** = srednje / upozorenje  
- **crvena** = loše / prioritet za pregled  
To ti pomaže da brzo skeniraš tabelu bez čitanja svakog reda.  
![](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAnEAAAACCAYAAAA3pIp+AAAABmJLR0QA/wD/AP+gvaeTAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAANElEQVR4nO3OQQmAABRAsSdYxKa/jL0MIR7FCt5E2BJsmZmt2gMA4C+Otbqr8+sJAACvXQ85SAYUQNBTfQAAAABJRU5ErkJggg==)  
**10. Filteri u rezultatima**  
Filteri su važni jer inače tabela može biti prevelika.  
**Najkorisniji filteri za početnike**  
**Nema sheme**  
Prikaži samo stranice koje nemaju Product / Offer structured data.  
Koristi kad želiš brzo naći:  
- mašinski nevidljive proizvode  
**Nema cijene**  
Prikaži samo stranice bez cijene.  
Koristi kad želiš brzo naći:  
- najkritičnije commerce probleme  
**Problem canonical**  
Prikaži stranice sa canonical mismatch problemima.  
Koristi kad želiš:  
- naći moguće probleme sa duplim sadržajem ili pogrešnim kanonskim linkovima  
**Noindex**  
Prikaži stranice koje ne bi trebale biti nevidljive pretraživačima.  
**Kategorija**  
Filtrira po izvučenoj kategoriji.  
**Ocjena min/max**  
Koristi kada želiš:  
- izdvojiti samo slabe ili samo jake stranice  
**Pretraga**  
Omogućava tekstualnu pretragu po:  
- URL-u  
- naslovu  
- SKU-u  
- GTIN-u  
- drugim dostupnim poljima  
![](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAnEAAAACCAYAAAA3pIp+AAAABmJLR0QA/wD/AP+gvaeTAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAANElEQVR4nO3OQQmAUBBAwSf8GGLWDWFDY3ixgjcRZhLMNjNHdQYAwF9cq1rV/vUEAIDX7gcRXAQ2s/16gwAAAABJRU5ErkJggg==)  
**11. Detalji stranice — desni panel**  
Kad klikneš na jedan red u tabeli, desno vidiš detalje.  
To je jedno od najvažnijih mjesta u aplikaciji.  
**Šta tu gledaš**  
**Osnovni podaci**  
- URL  
- naslov  
- H1  
- canonical  
- robots  
**Shema**  
Da li stranica ima:  
- Product schema  
- Offer schema  
- cijenu  
- valutu  
- dostupnost  
- SKU  
- GTIN  
- brand  
**Signali**  
- postoji li HTML cijena  
- postoji li shipping signal  
- postoji li returns signal  
- broj slika  
- dužina teksta  
**Oznake / problemi**  
Tu vidiš zašto je nešto označeno kao rizično.  
![](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAnEAAAACCAYAAAA3pIp+AAAABmJLR0QA/wD/AP+gvaeTAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAANUlEQVR4nO3OYQ1AABSAwY8JoIGqr4Z6Eoiggn9mu0twy8wc1RkAAH9xbdVa7V9PAAB47X4A9C4EIsmYmgsAAAAASUVORK5CYII=)  
**Kako koristiti detalje pametno**  
Najbolji način je:  
1. klikneš sumnjiv red  
2. vidiš šta konkretno nedostaje  
3. otvoriš stranicu u browseru  
4. uporediš stvarnu stranicu sa onim što je aplikacija našla  
Tako brzo vidiš da li je:  
- stvarni problem  
- ili problem detekcije  
![](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAnEAAAACCAYAAAA3pIp+AAAABmJLR0QA/wD/AP+gvaeTAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAANUlEQVR4nO3OMQ2AABAAsSNhZscYahheJwqQgQU2QtIq6DIze3UGAMBf3Gu1VcfXEwAAXrseoqcEQXyAWBgAAAAASUVORK5CYII=)  
**12. Akcije iz rezultata**  
**Otvori stranicu**  
Otvara odabrani URL u browseru.  
Koristi kad želiš:  
- ručno provjeriti stranicu  
- potvrditi problem  
- dati zadatak nekom drugom timu  
**Označi za ručnu reviziju**  
Prebacuje stranicu u tab **Red za reviziju**.  
Koristi kad želiš:  
- napraviti malu radnu listu  
- odvojiti važno od manje važnog  
**Izvezi odabrano**  
Izvozi odabrane redove u CSV.  
Koristi kad želiš:  
- poslati rezultate drugom timu  
- raditi dodatnu analizu u Excelu  
![](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAnEAAAACCAYAAAA3pIp+AAAABmJLR0QA/wD/AP+gvaeTAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAANUlEQVR4nO3OQQ2AQBAAsSE5CbzRujLwhwQMYIEfIWkVdJuZozoDAOAvrlWtav96AgDAa/cDEXQEKquakOYAAAAASUVORK5CYII=)  
**13. Tab “Red za reviziju” — kako se koristi**  
Ovo nije ista stvar kao glavni rezultat.  
Ovo je **radna lista kandidata** koje treba pregledati ručno.  
To su obično:  
- najproblematičnije stranice  
- sumnjive stranice  
- mali broj sample kandidata za poređenje  
![](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAnEAAAACCAYAAAA3pIp+AAAABmJLR0QA/wD/AP+gvaeTAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAANUlEQVR4nO3OQQmAABRAsSd49m4tA8nPaQJjWMGbCFuCLTOzV2cAAPzFvVZbdXw9AQDgtesBorcEPwOKyvQAAAAASUVORK5CYII=)  
**Statusi u redu za reviziju**  
Tipično ćeš vidjeti statuse kao:  
**Na čekanju**  
Stranica još nije pregledana.  
**Pregledano**  
Stranica je pogledana i ne traži dodatnu akciju.  
**Treba popravku**  
Problem je potvrđen i treba ga ispraviti.  
**Popravljeno**  
Problem je riješen.  
![](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAnEAAAACCAYAAAA3pIp+AAAABmJLR0QA/wD/AP+gvaeTAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAANUlEQVR4nO3OMQ2AABAAsSNBCUpfD6ZYGZDAgAU2QtIq6DIzW7UHAMBfHGt1V+fXEwAAXrseHCoGAe/SKtAAAAAASUVORK5CYII=)  
**Kako raditi kroz red za reviziju**  
Najjednostavniji tok:  
1. izaberi kandidata  
2. pročitaj detalje desno  
3. otvori stranicu u browseru  
4. potvrdi da li je problem stvaran  
5. napiši bilješku  
6. promijeni status  
7. pređi na sljedećeg kandidata  
Ako radiš u timu, ovaj tab je veoma koristan jer ti pomaže da ne zaboraviš:  
- šta je pregledano  
- šta stvarno treba popraviti  
- šta je već riješeno  
![](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAnEAAAACCAYAAAA3pIp+AAAABmJLR0QA/wD/AP+gvaeTAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAANUlEQVR4nO3OMQ2AABAAsSNhwgJmkPYLLpnRgQU2QtIq6DIze3UGAMBf3Gu1VcfHEQAA3rseaHkEMn1wK7sAAAAASUVORK5CYII=)  
**14. Izlazni fajlovi — šta znače**  
Nakon audita aplikacija pravi više fajlova.  
**products_raw.csv**  
Sirovi izvučeni podaci prije bodovanja.  
Koristi ga uglavnom:  
- developer  
- napredniji korisnik  
- neko ko želi dubinsku provjeru input podataka  
**products_scored.csv**  
Glavni audit CSV sa ocjenama i signalima.  
Ovo je najvažniji fajl za analizu.  
**manual_review_candidates.csv**  
Lista kandidata za ručnu reviziju.  
Obično manji, fokusiran skup URL-ova.  
**best_products_sample.csv**  
Uzorak dobrih stranica.  
Koristan za:  
- poređenje dobrih i loših primjera  
- benchmarking  
**category_summary.csv**  
Pregled po kategorijama.  
Koristan kad želiš:  
- vidjeti u kojim grupama proizvoda ima najviše problema  
**non_product_pages.csv**  
Stranice koje nisu prepoznate kao produktne.  
Koristan kad želiš:  
- provjeriti da li je filtering dobro odradio posao  
**errors.csv**  
Stranice koje nisu mogle biti preuzete ili obrađene.  
Koristan za:  
- tehnički troubleshooting  
**run_summary.json**  
Sažetak run-a:  
- koliko je obrađeno  
- koliko je trajalo  
- osnovna statistika  
![](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAnEAAAACCAYAAAA3pIp+AAAABmJLR0QA/wD/AP+gvaeTAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAANUlEQVR4nO3OMQ2AABAAsSPBCUZfE2IYmVDBhAU2QtIq6DIzW7UHAMBfnGt1V8fXEwAAXrse/xcF7U7sx4wAAAAASUVORK5CYII=)  
**15. Tipičan prvi audit — preporučeni tok rada**  
Ako aplikaciju koristiš prvi put, radi ovako:  
**Varijanta za prvi dan**  
1. pokreni aplikaciju  
2. unesi domen ili sitemap  
3. postavi **Max URL-ova = 10**  
4. ostavi ostale postavke na default  
5. pokreni skeniranje  
6. provjeri da li audit prolazi bez grešaka  
7. otvori rezultate  
8. pogledaj 2–3 problematične stranice  
9. pogledaj manual_review_candidates.csv  
10. pogledaj audit_report.docx ako je generisan  
**Varijanta za prvi ozbiljniji audit**  
1. unesi sitemap  
2. postavi **Max URL-ova = 50**  
3. ostavi delay i workers na default  
4. pokreni audit  
5. u rezultatima filtriraj:  
- Nema cijene  
- Nema sheme  
- Problem canonical  
6. označi najvažnije stranice za ručnu reviziju  
7. prođi kroz Red za reviziju  
8. izvezi rezultate  
9. podijeli CSV/report sa timom  
![](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAnEAAAACCAYAAAA3pIp+AAAABmJLR0QA/wD/AP+gvaeTAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAANklEQVR4nO3OQQmAABRAsSfYxZo/khWsYQLPJrCCNxG2BFtmZquOAAD4i3Ot7mr/egIAwGvXA4qjBdKlX6OKAAAAAElFTkSuQmCC)  
**16. Kako tumačiti rezultate ispravno**  
Ovo je važno:  
   
 **nije svaka niska ocjena automatski velika katastrofa.**  
Treba razlikovati:  
**Kritične probleme**  
To su stvari poput:  
- nema cijene  
- nema Product schema  
- stranica nije stvarno prepoznata kao produktna  
- canonical mismatch  
- važni komercijalni atributi nedostaju  
**Srednje probleme**  
To su stvari poput:  
- nema meta opisa  
- nema shipping signala  
- nema returns signala  
- schema je nepotpuna, ali postoji  
**Informativne nalaze**  
To su stranice koje nisu nužno loše, ali su korisne za poređenje.  
Zato shortlist i review red ne treba čitati kao:  
- “sve ovo je katastrofa”  
nego kao:  
- “ovo prvo pogledaj”  
![](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAnEAAAACCAYAAAA3pIp+AAAABmJLR0QA/wD/AP+gvaeTAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAANklEQVR4nO3OQQmAABRAsScYxpg/h5VMYARvRrCCNxG2BFtmZquOAAD4i3Ot7mr/egIAwGvXA224BcUMk6pDAAAAAElFTkSuQmCC)  
**17. Kad koristiti Playwright**  
Uključi Playwright samo ako vidiš znakove da običan HTML fetch ne vidi pravi sadržaj.  
Tipični simptomi:  
- aplikacija kaže da nema cijene, a u browseru se jasno vidi  
- aplikacija kaže da nema teksta, a stranica izgleda puna sadržaja  
- mnogo stranica izgleda prazno  
- webshop očigledno koristi SPA ili jači JS rendering  
Ako nema tih simptoma:  
- nemoj ga uključivati bez potrebe  
![](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAnEAAAACCAYAAAA3pIp+AAAABmJLR0QA/wD/AP+gvaeTAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAANUlEQVR4nO3OMQ2AABAAsSNBCUpfEJ5YGBDBgAU2QtIq6DIzW7UHAMBfHGt1V+fXEwAAXrseHDYF+yOk59sAAAAASUVORK5CYII=)  
**18. Najčešće greške početnika**  
**Greška 1 — skeniranje previše URL-ova odmah**  
Prvi run neka bude mali.  
**Greška 2 — uključivanje Playwright-a bez razloga**  
To samo usporava audit.  
**Greška 3 — čitanje ukupne ocjene bez gledanja razloga**  
Uvijek pogledaj detalje i oznake.  
**Greška 4 — ignorisanje review reda**  
Review red je najkorisniji dio za praktičan rad.  
**Greška 5 — zaključivanje iz premalog uzorka**  
10 URL-ova je dobro za test, ali nije dovoljno za velike zaključke o cijelom webshopu.  
![](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAnEAAAACCAYAAAA3pIp+AAAABmJLR0QA/wD/AP+gvaeTAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAANUlEQVR4nO3OQQmAABRAsSd49m4v6wg/pwmMYQVvImwJtszMXp0BAPAX91pt1fH1BACA164Hoq8EQMMPmF8AAAAASUVORK5CYII=)  
**19. Šta je normalno, a šta nije**  
**Normalno je da:**  
- audit traje nekoliko minuta  
- neke stranice završe u review redu  
- postoji mali broj sample kandidata  
- report pokaže nekoliko brzih “quick wins”  
**Nije normalno ako:**  
- audit stalno puca bez outputa  
- svi URL-ovi završe kao non-product  
- sve stranice navodno nemaju cijenu iako je to očigledno netačno  
- output fajlovi ne nastaju  
- review red izgleda potpuno besmisleno  
Ako se to desi, treba provjeriti:  
- sitemap ulaz  
- URL patterne  
- da li je potreban Playwright  
- log poruke iz taba Pokretanje  
![](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAnEAAAACCAYAAAA3pIp+AAAABmJLR0QA/wD/AP+gvaeTAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAANElEQVR4nO3OMQ0AIAwAwZIgBKnVgjN8dGDBABMhuZt+/JaZIyJmAADwi9VP1NMNAABu1AaU3AUhiyfJeAAAAABJRU5ErkJggg==)  
**20. Kako koristiti rezultate u praksi**  
Najbolji praktični pristup je ovaj:  
**Za SEO / ecommerce osobu**  
Fokus na:  
- nema cijene  
- nema schema  
- canonical problemi  
- meta opisi  
- category summary  
**Za developera**  
Fokus na:  
- errors.csv  
- products_raw.csv  
- structured data signale  
- canonical / robots / schema detalje  
**Za menadžera ili vlasnika shopa**  
Fokus na:  
- audit report  
- quick wins  
- review red  
- prioritetne stranice za popravku  
![](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAnEAAAACCAYAAAA3pIp+AAAABmJLR0QA/wD/AP+gvaeTAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAANklEQVR4nO3OMQ2AABAAsSNBCkLfFR7wwIgHRiywEZJWQZeZ2ao9AAD+4lyruzq+ngAA8Nr1AOIEBeX8aGZPAAAAAElFTkSuQmCC)  
**21. Preporučeni ritam rada**  
Ako audit radiš redovno, koristi ovaj ritam:  
**Sedmično**  
- mali audit uzorak  
- provjera novih problema  
**Mjesečno**  
- veći audit  
- poređenje sa prethodnim run-ovima  
**Nakon većih izmjena na webshopu**  
- obavezno ponovi audit  
- posebno ako su mijenjani:  
- template-i  
- structured data  
- URL struktura  
- produktni feedovi  
- frontend rendering  
![](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAnEAAAACCAYAAAA3pIp+AAAABmJLR0QA/wD/AP+gvaeTAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAANUlEQVR4nO3OMQ2AABAAsSNhwgJmkPYLLpnRgQU2QtIq6DIze3UGAMBf3Gu1VcfHEQAA3rseaHkEMn1wK7sAAAAASUVORK5CYII=)  
**22. Kratka checklista za prvog korisnika**  
**Prije audita**  
- imam domen ili sitemap  
- znam koliko URL-ova želim testirati  
- znam gdje će se sačuvati output  
**Tokom audita**  
- gledam progress  
- gledam log  
- ne prekidam bez potrebe  
**Poslije audita**  
- otvorim Results tab  
- filtriram “Nema cijene” i “Nema sheme”  
- pregledam Red za reviziju  
- otvorim output CSV/report  
![](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAnEAAAACCAYAAAA3pIp+AAAABmJLR0QA/wD/AP+gvaeTAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAANUlEQVR4nO3OQQmAABRAsSeYxKS/kJkED6bwYAVvImwJtszMVu0BAPAXx1rd1fn1BACA164HHDwF+DpPyKwAAAAASUVORK5CYII=)  
**23. Najkraće moguće objašnjenje aplikacije**  
Ako treba nekom objasniti u jednoj rečenici:  
**WebshopAudit je alat koji skenira produktne stranice webshopa, ocjenjuje koliko su tehnički, kataloški i komercijalno kvalitetne, i izdvaja prioritete za ručnu reviziju i popravke.**  
![](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAnEAAAACCAYAAAA3pIp+AAAABmJLR0QA/wD/AP+gvaeTAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAANElEQVR4nO3OQQmAABRAsad4EEtY9QcxnUms4E2ELcGWmTmrKwAA/uLeqrU6vp4AAPDa/gDzXgM37EF77AAAAABJRU5ErkJggg==)  
**24. Završna preporuka**  
Ako koristiš aplikaciju prvi put, radi ovim redom:  
1. mali run od 10 URL-ova  
2. provjera rezultata  
3. jedan run od 50 URL-ova  
4. review red  
5. eksport i izvještaj  
6. tek onda veći audit  
To je najbezbjedniji način da:  
- razumiješ alat  
- ne zatrpaš sebe rezultatima  
- i dobiješ stvarnu vrijednost iz aplikacije  
![](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAnEAAAACCAYAAAA3pIp+AAAABmJLR0QA/wD/AP+gvaeTAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAANklEQVR4nO3OMQ2AABAAsSNBACPq8MH2NpGACyywEZJWQZeZ2aszAAD+4l6rrTq+ngAA8Nr1AL/KBEe6dElaAAAAAElFTkSuQmCC)  
**25. Dodatna napomena**  
Ovo uputstvo je pisano za početnika.  
   
 Ako kasnije budeš radio sa aplikacijom redovno, preporučljivo je imati i:  
- kraće operativno uputstvo  
- tehničku arhitektonsku dokumentaciju  
- internu proceduru kako tim koristi review red i audit outpute  
