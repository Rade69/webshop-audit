"""
Entry point za GUI mod aplikacije.

Pokretanje:
    python -m gui.gui_main
    ili
    python -m gui.gui_main --config inputs/webshop_urls.txt

Odgovornost: Pokretanje PyQt6 aplikacije.
"""
import sys
from PyQt6.QtWidgets import QApplication

from gui.main_window import MainWindow


def main():
    """Glavna funkcija za GUI mod."""
    app = QApplication(sys.argv)
    app.setApplicationName("Webshop Audit")
    app.setOrganizationName("AuditTool")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()