"""
Kontroler za pokretanje audit run-a.

Odgovornost: Upravljanje AuditWorker-om i komunikacija sa UI-om.
Ova klasa je jedini posrednik između backend pipeline-a i GUI-a.
"""
import time
from datetime import datetime
from typing import Optional

from PyQt6.QtCore import QObject, QThread, pyqtSignal as Signal

from audit.pipeline import run_audit  # Import backend pipeline-a


class AuditWorker(QThread):
    """
    QThread worker za izvršavanje audit pipeline-a.

    Odgovornost: Pokretanje backend audit pipeline-a u zasebnoj niti
    i emitovanje signala za UI update.
    
    Ova klasa NE dirće UI direktno - samo emituje signale.
    Qt pravilo: UI se ažurira samo iz main threada.
    """

    # Faze pipeline-a
    phase_changed = Signal(str)
    # Vrijednosti: "url_collection" | "fetch" | "parse" | 
    #              "score" | "shortlist" | "export" | "done"

    # Progress
    progress_updated = Signal(int, int)
    # (processed_count, total_count)

    # Pojedinačni eventi
    url_fetched = Signal(str, bool)
    # (url, success)

    # Greška na pojedinačnom URL-u (ne fatalna)
    url_error = Signal(str, str)
    # (url, error_message)

    # Log poruke
    log_message = Signal(str, str)
    # (level, message) — level: "info" | "warning" | "error"

    # Statistike (ažuriraju se tokom runa)
    stats_updated = Signal(dict)
    # dict sa: total, processed, errors, non_product, candidates

    # Kraj runa
    run_completed = Signal(str)
    # output_dir path

    # Fatalna greška
    run_failed = Signal(str)
    # error_message

    def __init__(self, run_config: dict):
        """
        Args:
            run_config: Konfiguracija za audit run.
        """
        super().__init__()
        self.run_config = run_config
        self._stop_requested = False

    def request_stop(self):
        """
        Zahtijeva zaustavljanje workera.
        
        Worker će završiti trenutni URL i zatvoriti run.
        """
        self._stop_requested = True

    def run(self):
        """
        Glavna izvršna petlja workera.
        
        Pokreće backend audit pipeline i emituje signale za svaki event.
        """
        start_time = time.time()
        output_dir = ""
        
        try:
            self.phase_changed.emit("url_collection")
            self.log_message.emit("info", "Prikupljanje URL-ova...")
            
            # Kreiraj callback za progres
            def progress_callback(processed: int, total: int, phase: str):
                if self._stop_requested:
                    raise StopIteration("Stop requested")
                
                if phase:
                    self.phase_changed.emit(phase)
                
                self.progress_updated.emit(processed, total)
                
                # Ažuriraj statistike
                self.stats_updated.emit({
                    "total": total,
                    "processed": processed,
                    "errors": 0,  # Backend će ažurirati
                    "candidates": 0
                })
            
            # Kreiraj callback za log
            def log_callback(level: str, message: str):
                self.log_message.emit(level, message)
            
            # Pokreni audit pipeline
            self.log_message.emit("info", "Pokretanje audit pipeline-a...")
            
            result = run_audit(
                config=self.run_config,
                progress_callback=progress_callback,
                log_callback=log_callback
            )
            
            output_dir = result.get("output_dir", "")
            
            # Dodaj info ako je stopovan
            if self._stop_requested:
                self.log_message.emit("info", "Run zaustavljen od strane korisnika")
                self.stats_updated.emit({
                    "total": self.run_config.get("total_urls", 0),
                    "processed": result.get("processed", 0),
                    "errors": result.get("errors", 0),
                    "candidates": result.get("candidates", 0),
                    "stopped_early": True
                })
            
            elapsed = time.time() - start_time
            self.log_message.emit("info", f"Run završen za {elapsed:.1f}s")
            
            self.phase_changed.emit("done")
            self.run_completed.emit(output_dir)
            
        except StopIteration:
            # StopRequested - vratimo parcijalne rezultate
            self.log_message.emit("info", "Run zaustavljen - vraćam parcijalne rezultate")
            self.phase_changed.emit("done")
            self.run_completed.emit(output_dir or self.run_config.get("output_dir", ""))
            
        except Exception as e:
            self.log_message.emit("error", f"Fatalna greška: {str(e)}")
            self.run_failed.emit(str(e))


class AuditRunController(QObject):
    """
    Kontroler za upravljanje audit run-om.

    Odgovornost: 
    - Kreiranje i upravljanje AuditWorker-om
    - Prosljeđivanje signala iz workera ka UI-u
    - Čuvanje trenutnog stanja run-a
    
    Tabovi ne drže direktnu referencu na worker - komuniciraju samo
    preko ovog kontrolera.
    """

    # Forwarded worker signals (za tabove koji ne drže direktnu ref na workera)
    run_started = Signal()
    run_completed = Signal(str)   # output_dir
    run_failed = Signal(str)      # error
    phase_changed = Signal(str)
    progress_updated = Signal(int, int)
    log_message = Signal(str, str)
    stats_updated = Signal(dict)

    def __init__(self):
        super().__init__()
        self._worker: Optional[AuditWorker] = None
        self._run_config: Optional[dict] = None

    @property
    def is_running(self) -> bool:
        """Provjerava da li je worker aktivan."""
        return self._worker is not None and self._worker.isRunning()

    def start_run(self, run_config: dict):
        """
        Pokreće novi audit run.

        Args:
            run_config: Konfiguracija za audit run.
                Očekuje:
                - input_file: str - putanja do fajla sa URL-ovima
                - output_dir: str - putanja do output direktorijuma
                - config_options: dict - dodatne opcije
        """
        if self.is_running:
            self.log_message.emit("warning", "Run je već u toku!")
            return

        self._run_config = run_config
        self._worker = AuditWorker(run_config)

        # Poveži signale workera sa kontrolerovim signalima
        self._worker.phase_changed.connect(self.phase_changed)
        self._worker.progress_updated.connect(self.progress_updated)
        self._worker.log_message.connect(self.log_message)
        self._worker.stats_updated.connect(self.stats_updated)
        self._worker.run_completed.connect(self._on_worker_completed)
        self._worker.run_failed.connect(self._on_worker_failed)

        self.run_started.emit()
        self._worker.start()

    def stop_run(self):
        """Zahtijeva zaustavljanje trenutnog run-a."""
        if self._worker and self.is_running:
            self._worker.request_stop()
            self.log_message.emit("info", "Zahtjev za zaustavljanje poslat...")

    def get_current_state(self) -> "RunState":
        """
        Vraća trenutno stanje run-a.
        
        Returns:
            RunState sa trenutnim podacima.
        """
        from gui.viewmodels.run_state import RunState
        
        state = RunState()
        
        if self._worker is None:
            state.status = "idle"
        elif self._worker.isRunning():
            state.status = "running"
        elif self._run_config:
            state.status = "completed"
            state.output_dir = self._run_config.get("output_dir", "")
        
        return state

    def _on_worker_completed(self, output_dir: str):
        """Handluje završetak worker-a."""
        self.run_completed.emit(output_dir)
        # Čišćenje
        if self._worker:
            self._worker.deleteLater()
            self._worker = None

    def _on_worker_failed(self, error: str):
        """Handluje grešku worker-a."""
        self.run_failed.emit(error)
        # Čišćenje
        if self._worker:
            self._worker.deleteLater()
            self._worker = None