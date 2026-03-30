"""
ViewModel za stanje Run taba.

Odgovornost: Čuvanje i pristup podacima o trenutnom audit run-u.
Ovo je plain data klasa bez logike - samo struktura podataka.
"""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class RunState:
    """
    Stanje audit run-a.

    Atributi:
        status: Stanje run-a ("idle", "running", "completed", "failed", "stopped")
        phase: Trenutna faza pipeline-a ("url_collection", "fetch", "parse", ...)
        total_urls: Ukupan broj URL-ova za procesiranje
        processed: Broj obrađenih URL-ova
        errors: Broj grešaka
        candidates: Broj kandidata za kratku listu
        elapsed_seconds: Proteklo vrijeme u sekundama
        output_dir: Putanja do output direktorijuma
        stopped_early: Da li je run zaustavljen od strane korisnika
    """
    status: str = "idle"
    phase: str = ""
    total_urls: int = 0
    processed: int = 0
    errors: int = 0
    candidates: int = 0
    elapsed_seconds: float = 0.0
    output_dir: str = ""
    stopped_early: bool = False

    def reset(self):
        """Resetuje stanje na početne vrijednosti."""
        self.status = "idle"
        self.phase = ""
        self.total_urls = 0
        self.processed = 0
        self.errors = 0
        self.candidates = 0
        self.elapsed_seconds = 0.0
        self.output_dir = ""
        self.stopped_early = False

    def is_running(self) -> bool:
        """Provjerava da li je run u toku."""
        return self.status == "running"

    def is_idle(self) -> bool:
        """Provjerava da li je stanje idle."""
        return self.status == "idle"

    def progress_percent(self) -> float:
        """Računa procenat završenog posla."""
        if self.total_urls == 0:
            return 0.0
        return (self.processed / self.total_urls) * 100