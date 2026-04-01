# Prilagođeni agent dokumenti za projekat **WebshopAudit**

U ovoj arhivi nalaze se dvije prilagođene `.md` datoteke:

1. **AGENTS_webshop_audit.md**  
   Projektni standard i tvrda pravila za agente.

2. **CLAUDE_webshop_audit.md**  
   Operativne instrukcije kako agent treba čitati projekat, procjenjivati među-zavisnosti i isporučivati izmjene.

## Šta je prilagođeno u odnosu na stare fajlove

Ovi dokumenti više nisu pisani za ASYCUDA Pro, nego za **WebshopAudit**.

Najvažnije promjene:
- PySide6 je zamijenjen sa **PyQt6**
- Domenski modeli za carinske deklaracije uklonjeni su iz pravila
- LLM/Groq/Gemini pravila su uklonjena jer nisu centralni dio ovog projekta
- U fokus su stavljeni:
  - `ProductAuditRow`
  - score / flag kolone
  - drift između backend i GUI/report sloja
  - shortlist/review logika
  - usklađivanje `extractor → scorer → exporter → report → GUI`

## Kako ih koristiti

- Drži ih u root-u projekta ili u posebnom folderu za agent dokumentaciju
- Kada agentu daješ zadatak, uz prompt mu daj i jedan ili oba ova fajla
- Za refaktor i arhitekturu koristi prvenstveno **AGENTS_webshop_audit.md**
- Za dnevni operativni rad i stil isporuke koristi **CLAUDE_webshop_audit.md**

## Preporuka

Za svaki veći zadatak agentu dodaj i:
- koje fajlove smije dirati
- koje fajlove mora pregledati prije izmjene
- koje testove mora pokrenuti
- da ne smije uvoditi nove alias nazive kolona bez migracije
