"""
Kontroler za pokretanje audit run-a.

Odgovornost: Upravljanje AuditWorker-om i komunikacija sa UI-om.
Ova klasa je jedini posrednik između backend pipeline-a i GUI-a.
"""
import time
from typing import Optional

from PyQt6.QtCore import QObject, QThread, pyqtSignal as Signal

from audit.pipeline import run_audit
from audit.sitemap import discover_sitemap_urls, fetch_sitemap, collect_urls_from_sitemap, filter_product_like_urls


class SitemapLoadWorker(QThread):
    """
    QThread worker za učitavanje sitemap-a.

    Fetchuje sitemap, kolektuje URL-ove i filtrira product-like.
    Ako su proslijeđeni custom_patterns, koristi njih umjesto defaultnih.
    """

    sitemap_loaded = Signal(list, bool)   # (filtered_urls, used_fallback)
    sitemap_load_failed = Signal(str)     # error message

    def __init__(self, sitemap_url: str, custom_patterns: list[str] | None = None) -> None:
        super().__init__()
        self.sitemap_url = sitemap_url
        self.custom_patterns = custom_patterns  # None = koristi defaultne iz config.py

    def run(self) -> None:
        try:
            urls = collect_urls_from_sitemap(self.sitemap_url)

            if not urls:
                self.sitemap_load_failed.emit("No URLs found in sitemap.")
                return

            if self.custom_patterns:
                # Filtriraj prema korisničkim patternima
                filtered = [
                    u for u in urls
                    if any(p in u for p in self.custom_patterns)
                ]
                used_fallback = len(filtered) == 0
                self.sitemap_loaded.emit(filtered if not used_fallback else urls, used_fallback)
            else:
                # Defaultni heuristički filter
                filtered_urls, used_fallback = filter_product_like_urls(urls)
                self.sitemap_loaded.emit(filtered_urls, used_fallback)

        except Exception as e:
            self.sitemap_load_failed.emit(f"Error loading sitemap: {e}")


class SitemapDiscoverWorker(QThread):
    """
    QThread worker za autodiscover sitemap-a.

    Prolazi kroz listu kandidata i vraća prvi koji odgovori
    validnim XML-om. Blokira — mora se pokrenuti u zasebnoj niti.
    """

    discovered = Signal(str)   # pronađeni sitemap URL
    failed = Signal(str)       # poruka greške

    def __init__(self, domain: str) -> None:
        super().__init__()
        self.domain = domain

    def run(self) -> None:
        try:
            candidates = discover_sitemap_urls(self.domain)
            for url in candidates:
                xml = fetch_sitemap(url)
                if xml:
                    self.discovered.emit(url)
                    return
            self.failed.emit(
                f"Sitemap nije pronađen za '{self.domain}'. "
                "Provjerite domain ili unesite URL ručno."
            )
        except Exception as e:
            self.failed.emit(f"Greška pri autodiscoveru: {e}")


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

    # Sitemap autodiscover signali
    sitemap_discovered = Signal(str)   # pronađeni sitemap URL
    sitemap_discover_failed = Signal(str)  # poruka greške

    # Sitemap load signali
    sitemap_loaded = Signal(list, bool)   # (filtered_urls, used_fallback)
    sitemap_load_failed = Signal(str)    # error message

    def __init__(self):
        super().__init__()
        self._worker: Optional[AuditWorker] = None
        self._discover_worker: Optional[SitemapDiscoverWorker] = None
        self._load_worker: Optional[SitemapLoadWorker] = None
        self._run_config: Optional[dict] = None

        from gui.viewmodels.run_state import RunState
        self._state = RunState()

    @property
    def state(self) -> "RunState":
        """Persistentni RunState koji se ažurira kroz signale."""
        return self._state

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

        self._state.reset()
        self._state.status = "running"
        self.run_started.emit()
        self._worker.start()

    def discover_sitemap(self, domain: str) -> None:
        """
        Pokreće autodiscover sitemap-a za zadani domain u pozadini.

        Emituje sitemap_discovered(url) ako pronađe validan sitemap,
        ili sitemap_discover_failed(message) ako ništa ne pronađe.
        Ignorira poziv ako je discover već u toku.
        """
        if self._discover_worker and self._discover_worker.isRunning():
            return

        self._discover_worker = SitemapDiscoverWorker(domain)
        self._discover_worker.discovered.connect(self._on_sitemap_discovered)
        self._discover_worker.failed.connect(self._on_sitemap_discover_failed)
        self._discover_worker.start()

    def _on_sitemap_discovered(self, url: str) -> None:
        self.sitemap_discovered.emit(url)
        if self._discover_worker:
            self._discover_worker.deleteLater()
            self._discover_worker = None

    def _on_sitemap_discover_failed(self, message: str) -> None:
        self.sitemap_discover_failed.emit(message)
        if self._discover_worker:
            self._discover_worker.deleteLater()
            self._discover_worker = None

    def load_sitemap(self, sitemap_url: str, custom_patterns: list[str] | None = None) -> None:
        """
        Ucitava sitemap iz zadanog URL-a u pozadini.

        Args:
            sitemap_url: URL sitemap-a za ucitavanje.
            custom_patterns: Opcijski lista URL pod-stringova za filtriranje
                (npr. ['/oglas/', '/listing/']). None = defaultni heuristicki filter.
        Ignorira poziv ako je load vec u toku.
        """
        if self._load_worker and self._load_worker.isRunning():
            return

        self._load_worker = SitemapLoadWorker(sitemap_url, custom_patterns=custom_patterns)
        self._load_worker.sitemap_loaded.connect(self._on_sitemap_loaded)
        self._load_worker.sitemap_load_failed.connect(self._on_sitemap_load_failed)
        self._load_worker.start()

    def _on_sitemap_loaded(self, urls: list, used_fallback: bool) -> None:
        """Handluje uspješno učitavanje sitemap-a."""
        self.sitemap_loaded.emit(urls, used_fallback)
        if self._load_worker:
            self._load_worker.deleteLater()
            self._load_worker = None

    def _on_sitemap_load_failed(self, message: str) -> None:
        """Handluje grešku pri učitavanju sitemap-a."""
        self.sitemap_load_failed.emit(message)
        if self._load_worker:
            self._load_worker.deleteLater()
            self._load_worker = None

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
        self._state.status = "completed"
        self._state.output_dir = output_dir
        self.run_completed.emit(output_dir)
        if self._worker:
            self._worker.deleteLater()
            self._worker = None

    def _on_worker_failed(self, error: str):
        """Handluje grešku worker-a."""
        self._state.status = "failed"
        self.run_failed.emit(error)
        if self._worker:
            self._worker.deleteLater()
            self._worker = None