"""
Prilagođeni delegati za prikaz u tabelama.

Odgovornost: Crtanje score badge-ova, flag ćelija i status pill-ova.
Dizajn: Zaobljeni oblici, boje iz Soft Sage & Deep Blue palete.
"""
from PyQt6.QtWidgets import QStyledItemDelegate, QStyleOptionViewItem
from PyQt6.QtCore import Qt, QRectF, QSize
from PyQt6.QtGui import QPainter, QColor, QFont

from gui.styles.theme import COLORS


class ScoreDelegate(QStyledItemDelegate):
    """
    Delegate za prikaz numeričkih ocjena kao obojenih zaobljenih kvadrata.

    Boje prema pragu:
    - >= 70: zelena (#2E7D32)
    - 40–69: narandžasta (#FF8C00)
    - < 40:  crvena (#B53A3A)
    """

    def _badge_colors(self, score: int) -> tuple:
        """Vraća (bg, text) boje za zadatu ocjenu."""
        if score >= 70:
            return COLORS["score_high"], "#FFFFFF"
        elif score >= 40:
            return COLORS["score_mid"], "#FFFFFF"
        else:
            return COLORS["score_low"], "#FFFFFF"

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index):
        """Crta badge sa ocjenom."""
        score = index.data(Qt.ItemDataRole.DisplayRole)
        if not isinstance(score, (int, float)):
            super().paint(painter, option, index)
            return

        painter.save()

        bg_color, text_color = self._badge_colors(int(score))

        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QColor(bg_color))
        painter.setPen(Qt.PenStyle.NoPen)

        badge_w, badge_h = 48, 22
        bx = option.rect.x() + (option.rect.width() - badge_w) // 2
        by = option.rect.y() + (option.rect.height() - badge_h) // 2
        badge_rect = QRectF(bx, by, badge_w, badge_h)
        painter.drawRoundedRect(badge_rect, 5, 5)

        painter.setPen(QColor(text_color))
        font = QFont()
        font.setBold(True)
        font.setPointSize(10)
        painter.setFont(font)
        painter.drawText(badge_rect, Qt.AlignmentFlag.AlignCenter, str(int(score)))

        painter.restore()

    def sizeHint(self, _option, _index):
        return QSize(56, 32)


class StatusDelegate(QStyledItemDelegate):
    """
    Delegate za prikaz review statusa kao pill oblika sa bojama.

    Statusi (interni ključevi → srpski prikaz):
    - pending    → Na čekanju (siva)
    - needs_fix  → Treba popravku (crvena)
    - reviewed   → Pregledano (zelena)
    - fixed      → Popravljeno (plava #26629E)
    """

    # Interni engleski ključ → srpski prikaz u pill-u
    LABELS = {
        "pending":   "Na čekanju",     # "Pending"
        "needs_fix": "Treba popravku", # "Needs Fix"
        "reviewed":  "Pregledano",     # "Reviewed"
        "fixed":     "Popravljeno",    # "Fixed"
    }

    def _badge_colors(self, status: str) -> tuple:
        """Vraća (bg, text) boje za zadati status."""
        status_map = {
            "pending":   (COLORS["status_pending"],   "#FFFFFF"),
            "needs_fix": (COLORS["status_needs_fix"], "#FFFFFF"),
            "reviewed":  (COLORS["status_reviewed"],  "#FFFFFF"),
            "fixed":     (COLORS["status_fixed"],     "#FFFFFF"),
        }
        return status_map.get(status, (COLORS["text_secondary"], "#FFFFFF"))

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index):
        """Crta pill badge sa statusom."""
        status = index.data(Qt.ItemDataRole.DisplayRole) or "pending"

        painter.save()

        bg_color, text_color = self._badge_colors(status)

        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QColor(bg_color))
        painter.setPen(Qt.PenStyle.NoPen)

        # Visoki radius za pill oblik
        badge_w = min(110, option.rect.width() - 12)
        badge_h = 20
        bx = option.rect.x() + (option.rect.width() - badge_w) // 2
        by = option.rect.y() + (option.rect.height() - badge_h) // 2
        badge_rect = QRectF(bx, by, badge_w, badge_h)
        painter.drawRoundedRect(badge_rect, 10, 10)

        label = self.LABELS.get(status, status)
        painter.setPen(QColor(text_color))
        font = QFont()
        font.setBold(True)
        font.setPointSize(9)
        painter.setFont(font)
        # Fix: Use int for alignment flag, not AlignmentFlag enum
        painter.drawText(badge_rect, int(Qt.AlignmentFlag.AlignCenter), label)

        painter.restore()

    def sizeHint(self, _option, _index):
        return QSize(120, 32)


class FlagDelegate(QStyledItemDelegate):
    """
    Delegate za ćelije sa zastavicama — ističe probleme crvenom pozadinom.
    Ako je ćelija prazna/"-", nema istaknute pozadine.
    """

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index):
        """Crta ćeliju sa pozadinom ako postoje zastavice."""
        value = index.data(Qt.ItemDataRole.DisplayRole) or ""
        has_flags = value and value != "-"

        painter.save()

        if has_flags:
            painter.fillRect(option.rect, QColor("#FFF0F0"))
            text_color = COLORS["flag_error"]
        else:
            # Alternativna pozadina iz modela ako postoji, inače bijela
            bg = index.data(Qt.ItemDataRole.BackgroundRole)
            if bg:
                painter.fillRect(option.rect, bg)
            else:
                painter.fillRect(option.rect, QColor(COLORS["bg_table"]))
            text_color = COLORS["text_secondary"]

        painter.setPen(QColor(text_color))
        text_rect = option.rect.adjusted(8, 0, -4, 0)
        painter.drawText(
            text_rect,
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
            value
        )

        painter.restore()
