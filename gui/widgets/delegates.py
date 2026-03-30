"""
Custom delegates for table views.

Responsibility: Custom painting for score badges, flags, and status pills.
Focus on informative clarity over decoration.
"""
from PyQt6.QtWidgets import QStyledItemDelegate, QStyleOptionViewItem
from PyQt6.QtCore import Qt, QRectF, QSize
from PyQt6.QtGui import QPainter, QColor, QFont

from gui.styles.theme import COLORS


class ScoreDelegate(QStyledItemDelegate):
    """
    Delegate for rendering integer score values as colored rounded-rect badges.

    Colors:
    - >= 70: green (#5FA777)
    - 40-69: amber (#D9A441)
    - < 40: red (#C96A5A)
    """

    def _badge_colors(self, score: int) -> tuple:
        """Get background and text colors for score."""
        if score >= 70:
            return COLORS["score_high"], "#FFFFFF"
        elif score >= 40:
            return COLORS["score_mid"], "#FFFFFF"
        else:
            return COLORS["score_low"], "#FFFFFF"

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index):
        """Paint the score badge."""
        score = index.data(Qt.ItemDataRole.DisplayRole)
        if not isinstance(score, (int, float)):
            super().paint(painter, option, index)
            return

        painter.save()

        # Determine colors
        bg_color, text_color = self._badge_colors(int(score))

        # Draw background
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QColor(bg_color))
        painter.setPen(Qt.PenStyle.NoPen)

        # Draw rounded rect badge
        badge_w, badge_h = 48, 22
        bx = option.rect.x() + (option.rect.width() - badge_w) // 2
        by = option.rect.y() + (option.rect.height() - badge_h) // 2
        badge_rect = QRectF(bx, by, badge_w, badge_h)
        painter.drawRoundedRect(badge_rect, 4, 4)

        # Draw text
        painter.setPen(QColor(text_color))
        font = QFont()
        font.setBold(True)
        font.setPointSize(10)
        painter.setFont(font)
        painter.drawText(badge_rect, Qt.AlignmentFlag.AlignCenter, str(int(score)))

        painter.restore()

    def sizeHint(self, option, index):
        """Return size hint for the delegate."""
        return QSize(56, 28)


class StatusDelegate(QStyledItemDelegate):
    """
    Delegate for rendering review status as colored pill badges.

    Statuses:
    - pending: gray (#8A94A6)
    - needs_fix: red (#C96A5A)
    - reviewed: green (#5FA777)
    - fixed: blue (#4A90C2)
    """

    LABELS = {
        "pending": "Pending",
        "needs_fix": "Needs Fix",
        "reviewed": "Reviewed",
        "fixed": "Fixed",
    }

    def _badge_colors(self, status: str) -> tuple:
        """Get background and text colors for status."""
        status_map = {
            "pending": (COLORS["status_pending"], "#FFFFFF"),
            "needs_fix": (COLORS["status_needs_fix"], "#FFFFFF"),
            "reviewed": (COLORS["status_reviewed"], "#FFFFFF"),
            "fixed": (COLORS["status_fixed"], "#FFFFFF"),
        }
        return status_map.get(status, (COLORS["text_secondary"], "#FFFFFF"))

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index):
        """Paint the status pill badge."""
        status = index.data(Qt.ItemDataRole.DisplayRole) or "pending"

        painter.save()

        # Determine colors
        bg_color, text_color = self._badge_colors(status)

        # Draw pill shape
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QColor(bg_color))
        painter.setPen(Qt.PenStyle.NoPen)

        # High border radius for pill shape
        badge_w = min(80, option.rect.width() - 16)
        badge_h = 20
        bx = option.rect.x() + (option.rect.width() - badge_w) // 2
        by = option.rect.y() + (option.rect.height() - badge_h) // 2
        badge_rect = QRectF(bx, by, badge_w, badge_h)
        painter.drawRoundedRect(badge_rect, 10, 10)

        # Draw text
        label = self.LABELS.get(status, status)
        painter.setPen(QColor(text_color))
        font = QFont()
        font.setBold(True)
        font.setPointSize(9)
        painter.setFont(font)
        painter.drawText(badge_rect, Qt.AlignmentFlag.AlignCenter, label)

        painter.restore()

    def sizeHint(self, option, index):
        """Return size hint for the delegate."""
        return QSize(90, 26)


class FlagDelegate(QStyledItemDelegate):
    """
    Delegate for highlighting cells with non-empty flag strings.

    Applies subtle background color for flags without being "loud".
    """

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index):
        """Paint the flag cell with background if content exists."""
        value = index.data(Qt.ItemDataRole.DisplayRole) or ""

        painter.save()

        # Fill background based on content
        if value:
            # Subtle red background for flags
            painter.fillRect(option.rect, QColor("#FEF2F2"))
            text_color = COLORS["flag_error"]
        else:
            painter.fillRect(option.rect, QColor(COLORS["bg_table"]))
            text_color = COLORS["text_secondary"]

        # Draw text
        painter.setPen(QColor(text_color))
        text_rect = option.rect.adjusted(8, 0, -4, 0)
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, value)

        painter.restore()