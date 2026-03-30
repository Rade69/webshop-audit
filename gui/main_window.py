"""
Glavni prozor GUI aplikacije.

Odgovornost: 
- Kreiranje i upravljanje svim tabovima
- Kreiranje i upravljanje svim kontrolerima
- Posredovanje u inter-tab komunikaciji
- Prikazivanje status bar-a

Ovo je jedino mjesto gdje se tabovi kreiraju i vežu jedni za druge.
"""
from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtWidgets import (
    QMainWindow,
    QStatusBar,
    QTabWidget,
)

from gui.app_state import AppState
from gui.controllers.audit_run_controller import AuditRunController
from gui.controllers.results_controller import ResultsController
from gui.controllers.review_controller import ReviewController
from gui.tabs.input_tab import InputTab
from gui.tabs.run_tab import RunTab
from gui.tabs.results_tab import ResultsTab
from gui.tabs.review_queue_tab import ReviewQueueTab

from gui.styles.theme import apply_theme


class MainWindow(QMainWindow):
    """
    Glavni prozor aplikacije.

    Upravlja svim tabovima i kontrolerima.
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Webshop Audit")
        self.setMinimumSize(1000, 700)

        # Kreiraj kontrolere PRVI - tabovi će ih primati kao argumente
        self.audit_controller = AuditRunController()
        self.results_controller = ResultsController()
        self.review_controller = ReviewController()

        # Centralizirani pogled na stanje cijele aplikacije
        self.app_state = AppState(
            run_state=self.audit_controller.state,
            results_state=self.results_controller.state,
            review_state=self.review_controller.state,
        )

        # Kreiraj tabove i proslijedi kontrolere
        self._create_tabs()

        # Poveži inter-tab komunikaciju
        self._connect_inter_tab_signals()

        # Postavi UI
        self._setup_ui()

        # Status bar
        self._setup_status_bar()

        # Apply dark theme
        from PyQt6.QtWidgets import QApplication
        apply_theme(QApplication.instance())

    def _create_tabs(self):
        """Kreira sve tabove i povezuje ih sa kontrolerima."""
        # Input tab prima audit_controller za pokretanje run-a
        self.input_tab = InputTab(audit_controller=self.audit_controller)
        
        # Run tab prima audit_controller za prikaz progressa
        self.run_tab = RunTab(audit_controller=self.audit_controller)
        
        # Results tab prima results_controller za prikaz rezultata
        self.results_tab = ResultsTab(results_controller=self.results_controller)
        
        # Review Queue tab prima review_controller za prikaz liste za reviziju
        self.review_tab = ReviewQueueTab(review_controller=self.review_controller)

    def _setup_ui(self):
        """Postavlja UI komponente."""
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.TabPosition.North)

        # Dodaj tabove
        self.tab_widget.addTab(self.input_tab, "Input")
        self.tab_widget.addTab(self.run_tab, "Run")
        self.tab_widget.addTab(self.results_tab, "Results")
        self.tab_widget.addTab(self.review_tab, "Review Queue")

        self.setCentralWidget(self.tab_widget)

    def _setup_status_bar(self):
        """Postavlja status bar."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

    def _connect_inter_tab_signals(self):
        """Povezuje signale između tabova i kontrolera."""
        
        # Input tab - start scan request
        self.input_tab.start_scan_requested.connect(self._on_start_scan_requested)
        
        # Nakon završetka runa — automatski prebaci na Results tab
        self.audit_controller.run_completed.connect(self._on_run_completed)
        
        # Greška tokom runa
        self.audit_controller.run_failed.connect(self._on_run_failed)
        
        # Progress updates - ažuriraj status bar
        self.audit_controller.progress_updated.connect(self._on_progress_updated)
        
        # Phase changes - ažuriraj status bar
        self.audit_controller.phase_changed.connect(self._on_phase_changed)
        
        # Mark for Review u Results tabu dodaje u Review Queue
        self.results_controller.mark_for_review_requested.connect(
            self.review_controller.add_to_queue
        )

    @pyqtSlot(str)
    def _on_run_completed(self, output_dir: str):
        """
        Handler za završetak run-a.
        
        Prebacuje na Results tab i učitava rezultate.
        """
        # Učitaj rezultate u Results controller
        self.results_controller.load_results(output_dir)
        
        # Učitaj queue u Review controller
        self.review_controller.load_queue(output_dir)
        
        # Prebaci na Results tab
        self.tab_widget.setCurrentWidget(self.results_tab)
        
        self.status_bar.showMessage(f"Completed — {output_dir}")

    @pyqtSlot(str)
    def _on_run_failed(self, error: str):
        """Handler za grešku tokom run-a."""
        self.status_bar.showMessage(f"Error: {error}")

    @pyqtSlot(int, int)
    def _on_progress_updated(self, processed: int, total: int):
        """Handler za ažuriranje progressa."""
        if total > 0:
            self.status_bar.showMessage(f"Scanning... {processed}/{total}")

    @pyqtSlot(str)
    def _on_phase_changed(self, phase: str):
        """Handler za promjenu faze."""
        phase_display = {
            "url_collection": "Prikupljanje URL-ova",
            "fetch": "Preuzimanje stranica",
            "parse": "Parsiranje",
            "score": "Bodovanje",
            "shortlist": "Kratka lista",
            "export": "Izvoz",
            "done": "Završeno"
        }.get(phase, phase)
        
        self.status_bar.showMessage(phase_display)

    @pyqtSlot(dict)
    def _on_start_scan_requested(self, config: dict):
        """
        Handler za zahtjev za pokretanje scan-a.
        
        Pokreće audit run i prebacuje na Run tab.
        """
        # Start the audit run through controller
        self.audit_controller.start_run(config)
        
        # Switch to Run tab
        self.tab_widget.setCurrentWidget(self.run_tab)
        
        self.status_bar.showMessage("Starting scan...")