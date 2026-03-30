"""
Custom widgets for the GUI application.

Responsibility: Reusable custom widgets like ScoreBadge.
"""
from PyQt6.QtWidgets import QLabel
from PyQt6.QtCore import Qt

from gui.styles.theme import COLORS


class ScoreBadge(QLabel):
    """
    Badge widget for displaying score values.

    Displays a score number in a colored rounded rectangle:
    - Green (score_high) for scores >= 70
    - Yellow (score_mid) for scores 40-69
    - Red (score_low) for scores < 40
    """

    def __init__(self, score: int = 0, parent=None):
        """
        Initialize ScoreBadge.

        Args:
            score: Initial score value (0-100).
            parent: Parent widget.
        """
        super().__init__(parent)
        self.setFixedSize(48, 24)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.set_score(score)

    def set_score(self, score: int) -> None:
        """
        Set the score value and update background color.

        Args:
            score: Score value (0-100).
        """
        if score is None or not isinstance(score, int):
            score = 0

        # Determine color based on score
        if score >= 70:
            color = COLORS["score_high"]
        elif score >= 40:
            color = COLORS["score_mid"]
        else:
            color = COLORS["score_low"]

        # Set stylesheet with rounded corners
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {color};
                color: white;
                font-weight: bold;
                border-radius: 4px;
            }}
        """)
        self.setText(str(score))