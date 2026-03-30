"""
Centralizirani app state.

Odgovornost: Pruža jednu tačku pristupa svim state objektima
aplikacije. Koristi se u MainWindow-u i svuda gdje je potreban
globalni pogled na stanje (npr. serijalizacija za checkpoint,
debug, testovi).
"""
from gui.viewmodels.run_state import RunState
from gui.viewmodels.results_state import ResultsState
from gui.viewmodels.review_state import ReviewState


class AppState:
    """
    Facade koja agregira stanje sva tri podsistema.

    Ne zamjenjuje kontrolere — samo pruža read-only pogled
    na njihove state objekte bez direktnog spajanja na UI logiku.

    Attributes:
        run: Stanje trenutnog audit run-a (RunState).
        results: Stanje Results taba (ResultsState).
        review: Stanje Review Queue taba (ReviewState).
    """

    def __init__(
        self,
        run_state: RunState,
        results_state: ResultsState,
        review_state: ReviewState,
    ) -> None:
        self.run = run_state
        self.results = results_state
        self.review = review_state

    def is_busy(self) -> bool:
        """True dok audit run teče."""
        return self.run.is_running()

    def is_ready_for_export(self) -> bool:
        """True kad su rezultati učitani i nije aktivan run."""
        return self.results.is_loaded() and not self.is_busy()

    def summary(self) -> dict:
        """Compact dict za logging/debug."""
        return {
            "run_status": self.run.status,
            "run_phase": self.run.phase,
            "total_urls": self.run.total_urls,
            "processed": self.run.processed,
            "results_loaded": self.results.is_loaded(),
            "results_count": self.results.total_count,
            "review_pending": self.review.pending_count,
        }
