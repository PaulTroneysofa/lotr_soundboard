#!/usr/bin/env python3
"""Soundboard Le Seigneur des Anneaux — version française."""

import math
import os
import sys
import time

os.environ.setdefault("SDL_AUDIODRIVER", "pulse,alsa,dummy")
os.environ.setdefault("SDL_VIDEODRIVER", "x11,wayland,offscreen")

import pygame
from PyQt5.QtCore import Qt, QThread, QTimer, pyqtSignal
from PyQt5.QtGui import (
    QColor,
    QCursor,
    QFont,
    QKeySequence,
    QPalette,
)
from PyQt5.QtWidgets import (
    QApplication,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QShortcut,
    QSizePolicy,
    QSlider,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

SOUNDS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sounds")

# ── Palette ──────────────────────────────────────────────────────────────────
BG_DEEP = "#06050A"  # quasi-noir avec teinte froide
BG_PANEL = "#0D0B12"  # sidebar
BG_CARD = "#13101A"  # carte son
BG_CARD_HOVER = "#1C1826"  # carte survolée
GOLD = "#C8A040"  # or de l'Anneau
GOLD_BRIGHT = "#E8C060"  # or vif
GOLD_DIM = "#7A6020"  # or atténué
SILVER = "#A0B0C0"  # argent elfique
TEXT_MAIN = "#E8DEC8"  # parchemin clair
TEXT_DIM = "#6A6050"  # parchemin sombre
DIVIDER = "#1E1A28"  # séparateur

CHARACTERS = {
    "Gimli": {
        "emoji": "⚒",
        "accent": "#B04010",
        "glow": "#FF6020",
        "tag": "Nain du Glitter Rock",
        "sounds": [
            ("et_ma_hache", "Et ma hache !"),
            ("personne_ne_jette_un_nain", "Personne ne jette un nain !"),
            ("gloire_a_la_moria", "Gloire à la Moria !"),
            ("aucune_honte_davoir_peur", "Je n'ai aucune honte d'avoir peur !"),
            ("que_ca_serve_de_lecon", "Que ça serve de leçon !"),
            ("ma_langue_sur_des_marches_glacees", "Ma langue sur des marches glacées..."),
        ],
    },
    "Gandalf": {
        "emoji": "✦",
        "accent": "#4A6878",
        "glow": "#80C0E0",
        "tag": "Istari — Le Blanc",
        "sounds": [
            ("vous_ne_passerez_pas", "Vous ne passerez pas !"),
            ("tu_ne_peux_pas_passer", "Tu ne peux pas passer !"),
            ("fuyez_pauvres_fous", "Fuyez, pauvres fous !"),
            ("je_suis_gandalf_le_blanc", "Je suis Gandalf le Blanc !"),
            (
                "arrive_precisement_quand_il_le_decide",
                "Un magicien arrive précisément quand il le décide",
            ),
        ],
    },
    "Aragorn": {
        "emoji": "⚔",
        "accent": "#284060",
        "glow": "#6090C0",
        "tag": "Héritier d'Isildur",
        "sounds": [
            ("ce_jour_nest_pas_encore_venu", "Ce jour n'est pas encore venu !"),
            ("pour_frodon", "Pour Frodon !"),
            ("mourons_ensemble", "Alors, mourons ensemble !"),
            ("pas_encore_vivants", "Ils ne sont pas encore vivants !"),
            ("roi_elessar", "Roi Elessar !"),
        ],
    },
    "Legolas": {
        "emoji": "◈",
        "accent": "#1A5030",
        "glow": "#40C060",
        "tag": "Prince des Elfes Sylvains",
        "sounds": [
            ("ils_vont_a_isengard", "Ils vont à Isengard !"),
            ("soixante_dix_fleches", "J'avais soixante-dix flèches !"),
            ("mon_arc_est_pret", "Mon arc est prêt !"),
            ("trois_jours_sans_dormir", "Trois jours sans dormir..."),
        ],
    },
    "Frodon": {
        "emoji": "◎",
        "accent": "#5A3810",
        "glow": "#C08040",
        "tag": "Porteur de l'Anneau",
        "sounds": [
            ("je_prends_lanneau", "Je prends l'Anneau !"),
            ("je_voudrais_que_cette_nuit", "Je voudrais que cette nuit n'ait jamais commencé"),
            ("porteur_de_lanneau", "Porteur de l'Anneau"),
            ("je_suis_heureux_que_tu_sois_la", "Je suis heureux que tu sois là, Sam"),
        ],
    },
    "Sam": {
        "emoji": "❧",
        "accent": "#4A4000",
        "glow": "#C0A800",
        "tag": "Jardinier du Comté",
        "sounds": [
            ("je_peux_vous_porter", "Je ne peux pas porter l'Anneau... mais je peux vous porter !"),
            ("la_lumiere_le_sera_toujours", "La lumière le sera toujours"),
            ("monsieur_frodon", "Monsieur Frodon !"),
            ("taters_les_pommes_de_terre", "Les taters ! Les pommes de terre !"),
        ],
    },
    "Gollum": {
        "emoji": "◉",
        "accent": "#102808",
        "glow": "#30A020",
        "tag": "Ancien Porteur",
        "sounds": [
            ("mon_precieux", "Mon Précieux !"),
            ("nous_voulons_ca", "Nous voulons ça, on veut..."),
            ("nous_haissons_baggins", "Nous haïssons Baggins !"),
            ("pas_de_lembas_pour_nous", "Pas de lembas pour nous !"),
        ],
    },
    "Saruman": {
        "emoji": "✧",
        "accent": "#400050",
        "glow": "#C040E0",
        "tag": "Chef des Istari",
        "sounds": [
            ("la_terre_du_milieu_tombera", "La Terre du Milieu tombera !"),
            ("ordre_des_istari", "L'Ordre des Istari"),
            ("palantir", "Le Palantír ne ment pas"),
        ],
    },
}


# ── Audio ─────────────────────────────────────────────────────────────────────


class AudioThread(QThread):
    finished = pyqtSignal(int)
    error = pyqtSignal(str, int)
    progress = pyqtSignal(float)

    def __init__(self, path: str, gen_id: int, volume: float) -> None:
        super().__init__()
        self.path = path
        self.gen_id = gen_id
        self._volume = volume

    def run(self) -> None:
        try:
            sound = pygame.mixer.Sound(self.path)
            sound.set_volume(self._volume)
            duration_ms = sound.get_length() * 1000
            channel = sound.play()
            if channel is None:
                self.error.emit("Aucun canal audio disponible", self.gen_id)
                return
            start = time.monotonic()
            while channel.get_busy():
                elapsed = (time.monotonic() - start) * 1000
                if duration_ms > 0:
                    self.progress.emit(min(elapsed / duration_ms, 1.0))
                self.msleep(30)
            self.progress.emit(1.0)
            self.finished.emit(self.gen_id)
        except Exception as e:
            self.error.emit(str(e), self.gen_id)


# ── Widgets ───────────────────────────────────────────────────────────────────


class GoldDivider(QFrame):
    """Fine ligne décorative dorée."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setFixedHeight(1)
        self.setStyleSheet(
            f"background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 {BG_PANEL}, stop:0.3 {GOLD_DIM}, stop:0.7 {GOLD_DIM}, stop:1 {BG_PANEL});"
        )


class CharacterButton(QPushButton):
    """Bouton de sélection de personnage dans la sidebar."""

    def __init__(self, name: str, data: dict, parent=None) -> None:
        super().__init__(parent)
        self.char_name = name
        self.accent = data["accent"]
        self.glow_color = data["glow"]
        self._selected = False
        self.setFixedHeight(64)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self._build_content(name, data)
        self._apply_style(False)

    def _build_content(self, name: str, data: dict) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 0, 14, 0)
        layout.setSpacing(12)

        emoji = QLabel(data["emoji"])
        emoji.setFont(QFont("DejaVu Sans", 16))
        emoji.setFixedWidth(28)
        emoji.setAlignment(Qt.AlignCenter)
        emoji.setAttribute(Qt.WA_TransparentForMouseEvents)
        layout.addWidget(emoji)

        text_col = QVBoxLayout()
        text_col.setSpacing(1)

        name_lbl = QLabel(name)
        name_lbl.setFont(QFont("DejaVu Serif", 11, QFont.Bold))
        name_lbl.setAttribute(Qt.WA_TransparentForMouseEvents)

        tag_lbl = QLabel(data["tag"])
        tag_lbl.setFont(QFont("DejaVu Sans", 8))
        tag_lbl.setAttribute(Qt.WA_TransparentForMouseEvents)

        text_col.addWidget(name_lbl)
        text_col.addWidget(tag_lbl)
        layout.addLayout(text_col)
        layout.addStretch()

        self._name_lbl = name_lbl
        self._tag_lbl = tag_lbl

    def _apply_style(self, selected: bool) -> None:
        self._selected = selected
        if selected:
            left_border = f"border-left: 3px solid {self.glow_color};"
            bg = f"background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 {self.accent}AA, stop:1 {BG_PANEL});"
            name_color = GOLD_BRIGHT
            tag_color = SILVER
        else:
            left_border = "border-left: 3px solid transparent;"
            bg = "background: transparent;"
            name_color = TEXT_MAIN
            tag_color = TEXT_DIM

        self.setStyleSheet(f"""
            QPushButton {{
                {bg}
                border: none;
                {left_border}
                border-radius: 0px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 {self.accent}55, stop:1 {BG_PANEL});
                border-left: 3px solid {GOLD_DIM};
            }}
        """)
        self._name_lbl.setStyleSheet(f"color: {name_color}; background: transparent;")
        self._tag_lbl.setStyleSheet(f"color: {tag_color}; background: transparent;")

    def set_selected(self, selected: bool) -> None:
        self._apply_style(selected)


class SoundCard(QPushButton):
    """Carte de son cliquable — le cœur du soundboard."""

    def __init__(
        self, label: str, key: str, path: str, accent: str, glow: str, index: int, parent=None
    ) -> None:
        super().__init__(parent)
        self.path = path
        self.accent = accent
        self.glow_color = glow
        self._playing = False
        self.setMinimumHeight(72)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setEnabled(os.path.exists(path))
        self._build(label, index)
        self._apply_style(False)

    def _build(self, label: str, index: int) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(14)

        # Numéro de touche
        if index < 9:
            idx_lbl = QLabel(str(index + 1))
            idx_lbl.setFixedSize(22, 22)
            idx_lbl.setAlignment(Qt.AlignCenter)
            idx_lbl.setFont(QFont("DejaVu Sans", 8, QFont.Bold))
            idx_lbl.setStyleSheet(f"""
                color: {GOLD};
                background: {BG_DEEP};
                border: 1px solid {GOLD_DIM};
                border-radius: 4px;
            """)
            idx_lbl.setAttribute(Qt.WA_TransparentForMouseEvents)
            layout.addWidget(idx_lbl)

        text_col = QVBoxLayout()
        text_col.setSpacing(2)

        quote = QLabel(f"« {label} »")
        quote.setFont(QFont("DejaVu Serif", 10))
        quote.setWordWrap(True)
        quote.setAttribute(Qt.WA_TransparentForMouseEvents)

        fname = os.path.splitext(os.path.basename(self.path))[0].replace("_", " ")
        hint = QLabel(fname)
        hint.setFont(QFont("DejaVu Sans", 8))
        hint.setAttribute(Qt.WA_TransparentForMouseEvents)

        text_col.addWidget(quote)
        text_col.addWidget(hint)
        layout.addLayout(text_col)
        layout.addStretch()

        # Indicateur lecture
        self._play_dot = QLabel("▶")
        self._play_dot.setFixedWidth(18)
        self._play_dot.setAlignment(Qt.AlignCenter)
        self._play_dot.setFont(QFont("DejaVu Sans", 10))
        self._play_dot.setStyleSheet(f"color: {GOLD}; background: transparent;")
        self._play_dot.setVisible(False)
        self._play_dot.setAttribute(Qt.WA_TransparentForMouseEvents)
        layout.addWidget(self._play_dot)

        self._quote = quote
        self._hint = hint

    def _apply_style(self, playing: bool) -> None:
        if not self.isEnabled():
            self.setStyleSheet(f"""
                QPushButton {{
                    background: {BG_CARD};
                    border: 1px solid {DIVIDER};
                    border-radius: 8px;
                    color: {TEXT_DIM};
                }}
            """)
            return

        if playing:
            border = f"border: 1px solid {self.glow_color};"
            bg = f"background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 {self.accent}CC, stop:1 {BG_CARD});"
            q_color = GOLD_BRIGHT
        else:
            border = f"border: 1px solid {DIVIDER};"
            bg = f"background: {BG_CARD};"
            q_color = TEXT_MAIN

        self.setStyleSheet(f"""
            QPushButton {{
                {bg}
                {border}
                border-radius: 8px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                    stop:0 {self.accent}88, stop:1 {BG_CARD_HOVER});
                border: 1px solid {GOLD_DIM};
            }}
            QPushButton:pressed {{
                background: {self.accent};
                border: 1px solid {self.glow_color};
            }}
        """)
        self._quote.setStyleSheet(f"color: {q_color}; background: transparent;")
        self._hint.setStyleSheet(f"color: {TEXT_DIM}; background: transparent; font-style: italic;")
        self._play_dot.setVisible(playing)

    def set_playing(self, playing: bool) -> None:
        if self._playing == playing:
            return
        self._playing = playing
        self._apply_style(playing)


class PulseLabel(QLabel):
    _STEPS = 40

    def __init__(self, text: str, parent=None) -> None:
        super().__init__(text, parent)
        self._step = 0
        self._dir = 1
        self._timer = QTimer(self)
        self._timer.setInterval(25)
        self._timer.timeout.connect(self._tick)
        self._apply(1.0)

    def start_pulse(self) -> None:
        self._step = 0
        self._dir = 1
        self._timer.start()

    def stop_pulse(self) -> None:
        self._timer.stop()
        self._apply(1.0)

    def _tick(self) -> None:
        self._step += self._dir
        self._apply(0.4 + 0.6 * abs(math.sin(math.pi * self._step / self._STEPS)))
        if self._step >= self._STEPS:
            self._dir = -1
        elif self._step <= 0:
            self._dir = 1

    def _apply(self, b: float) -> None:
        r, g, bl = int(232 * b), int(192 * b), int(96 * b)
        self.setStyleSheet(
            f"color: rgb({r},{g},{bl}); background: transparent; font-style: italic;"
        )


class CharacterPanel(QWidget):
    play_sound = pyqtSignal(str, object)

    def __init__(self, name: str, data: dict, parent=None) -> None:
        super().__init__(parent)
        self.name = name
        self.data = data
        self.cards: dict[str, SoundCard] = {}
        self._shortcuts: list[QShortcut] = []
        self.setStyleSheet(f"background: {BG_DEEP};")
        self._build()

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(0)

        # En-tête personnage
        header = QWidget()
        header.setStyleSheet("background: transparent;")
        h_layout = QVBoxLayout(header)
        h_layout.setContentsMargins(0, 0, 0, 0)
        h_layout.setSpacing(4)

        emoji_name = QHBoxLayout()
        emoji_name.setSpacing(12)

        e_lbl = QLabel(self.data["emoji"])
        e_lbl.setFont(QFont("DejaVu Sans", 28))
        e_lbl.setStyleSheet(f"color: {self.data['glow']}; background: transparent;")
        emoji_name.addWidget(e_lbl)

        name_block = QVBoxLayout()
        name_block.setSpacing(2)
        n_lbl = QLabel(self.name)
        n_lbl.setFont(QFont("DejaVu Serif", 22, QFont.Bold))
        n_lbl.setStyleSheet(f"color: {GOLD_BRIGHT}; background: transparent;")
        t_lbl = QLabel(self.data["tag"])
        t_lbl.setFont(QFont("DejaVu Sans", 10))
        t_lbl.setStyleSheet(f"color: {SILVER}; background: transparent; letter-spacing: 2px;")
        name_block.addWidget(n_lbl)
        name_block.addWidget(t_lbl)
        emoji_name.addLayout(name_block)
        emoji_name.addStretch()

        count_lbl = QLabel(f"{len(self.data['sounds'])} répliques")
        count_lbl.setFont(QFont("DejaVu Sans", 9))
        count_lbl.setStyleSheet(f"color: {TEXT_DIM}; background: transparent;")
        count_lbl.setAlignment(Qt.AlignRight | Qt.AlignBottom)
        emoji_name.addWidget(count_lbl)

        h_layout.addLayout(emoji_name)
        root.addWidget(header)

        # Ligne dorée
        div = GoldDivider()
        root.addSpacing(16)
        root.addWidget(div)
        root.addSpacing(20)

        # Scroll + grille de cartes
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet(f"""
            QScrollArea {{ background: {BG_DEEP}; border: none; }}
            QScrollBar:vertical {{
                background: {BG_PANEL}; width: 6px; border-radius: 3px;
            }}
            QScrollBar::handle:vertical {{
                background: {GOLD_DIM}; border-radius: 3px; min-height: 30px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
        """)

        grid_w = QWidget()
        grid_w.setStyleSheet(f"background: {BG_DEEP};")
        grid = QVBoxLayout(grid_w)
        grid.setSpacing(10)
        grid.setContentsMargins(0, 0, 8, 0)

        for i, (key, label) in enumerate(self.data["sounds"]):
            path = os.path.join(SOUNDS_DIR, self.name.lower(), f"{key}.wav")
            card = SoundCard(label, key, path, self.data["accent"], self.data["glow"], i)
            if card.isEnabled():
                card.clicked.connect(lambda _, p=path, c=card: self.play_sound.emit(p, c))
            else:
                card.setToolTip(f"Fichier audio manquant :\n{path}")
            shadow = QGraphicsDropShadowEffect()
            shadow.setBlurRadius(12)
            shadow.setOffset(0, 2)
            shadow.setColor(QColor(0, 0, 0, 120))
            card.setGraphicsEffect(shadow)
            self.cards[key] = card
            grid.addWidget(card)

        grid.addStretch()
        scroll.setWidget(grid_w)
        root.addWidget(scroll, 1)

    def install_shortcuts(self, window: QWidget) -> None:
        for sc in self._shortcuts:
            sc.setEnabled(False)
        self._shortcuts.clear()
        for i, card in enumerate(self.cards.values()):
            if i >= 9 or not card.isEnabled():
                continue
            sc = QShortcut(QKeySequence(str(i + 1)), window)
            sc.activated.connect(card.click)
            self._shortcuts.append(sc)

    def filter(self, text: str) -> None:
        t = text.lower()
        for card in self.cards.values():
            card.setVisible(not t or t in card._quote.text().lower())

    def reset_cards(self) -> None:
        for card in self.cards.values():
            card.set_playing(False)


# ── Fenêtre principale ────────────────────────────────────────────────────────


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Le Seigneur des Anneaux — Soundboard VF")
        self.setMinimumSize(1000, 640)
        self._gen_id = 0
        self._current_thread: AudioThread | None = None
        self._current_card: SoundCard | None = None
        self._volume = 0.80
        self._char_buttons: dict[str, CharacterButton] = {}
        self._panels: dict[str, CharacterPanel] = {}
        self._active_char: str = list(CHARACTERS.keys())[0]
        self._setup_audio()
        self._build_ui()
        self._apply_theme()
        self._select_character(self._active_char)
        self._setup_shortcuts()

    # ── audio ──────────────────────────────────────────────────────────────

    def _setup_audio(self) -> None:
        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)
            pygame.mixer.set_num_channels(8)
        except Exception as e:
            print(f"[audio] {e}")

    def _stop(self) -> None:
        pygame.mixer.stop()
        self._gen_id += 1
        if self._current_card:
            self._current_card.set_playing(False)
            self._current_card = None
        self._progress.setValue(0)
        self._now_playing.setText("—")
        self._now_playing.stop_pulse()
        self.status.showMessage("Arrêté")

    def _play(self, path: str, card: SoundCard) -> None:
        if not os.path.exists(path):
            self.status.showMessage(f"⚠  Fichier introuvable : {path}")
            return
        pygame.mixer.stop()
        self._gen_id += 1
        gen = self._gen_id
        if self._current_card:
            self._current_card.set_playing(False)
        card.set_playing(True)
        self._current_card = card
        char = os.path.basename(os.path.dirname(path)).capitalize()
        label = card._quote.text()
        self._now_playing.setText(label)
        self._now_playing.start_pulse()
        self._progress.setValue(0)
        self.status.showMessage(f"▶  {char}  —  {label}")
        self._current_thread = AudioThread(path, gen, self._volume)
        self._current_thread.finished.connect(self._on_finished)
        self._current_thread.error.connect(self._on_error)
        self._current_thread.progress.connect(self._on_progress)
        self._current_thread.start()

    def _on_finished(self, gen_id: int) -> None:
        if gen_id != self._gen_id:
            return
        if self._current_card:
            self._current_card.set_playing(False)
            self._current_card = None
        self._progress.setValue(0)
        self._now_playing.setText("—")
        self._now_playing.stop_pulse()
        self.status.showMessage("Prêt")

    def _on_error(self, msg: str, gen_id: int) -> None:
        if gen_id != self._gen_id:
            return
        if self._current_card:
            self._current_card.set_playing(False)
            self._current_card = None
        self._now_playing.setText("—")
        self._now_playing.stop_pulse()
        self.status.showMessage(f"⚠  {msg}")

    def _on_progress(self, ratio: float) -> None:
        self._progress.setValue(int(ratio * 100))

    def _on_volume(self, v: int) -> None:
        self._volume = v / 100
        self._vol_pct.setText(f"{v}%")

    # ── UI ─────────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        root = QWidget()
        self.setCentralWidget(root)
        root.setStyleSheet(f"background: {BG_DEEP};")
        layout = QHBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(self._build_sidebar())

        right = QVBoxLayout()
        right.setContentsMargins(0, 0, 0, 0)
        right.setSpacing(0)
        right.addWidget(self._build_topbar())
        right.addWidget(self._build_nowplaying())
        right.addWidget(self._build_panel_stack(), 1)

        right_w = QWidget()
        right_w.setLayout(right)
        right_w.setStyleSheet(f"background: {BG_DEEP};")
        layout.addWidget(right_w, 1)

        self.status = QStatusBar()
        self.status.setStyleSheet(
            f"background: {BG_PANEL}; color: {TEXT_DIM}; font-size: 10px; "
            f"border-top: 1px solid {DIVIDER}; padding: 0 8px;"
        )
        self.setStatusBar(self.status)
        self.status.showMessage("Prêt — choisissez un personnage et cliquez sur une réplique")

    def _build_sidebar(self) -> QWidget:
        sidebar = QWidget()
        sidebar.setFixedWidth(220)
        sidebar.setStyleSheet(f"background: {BG_PANEL}; border-right: 1px solid {DIVIDER};")

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Logo
        logo = QLabel("⚔  LOTR\nSoundboard")
        logo.setFont(QFont("DejaVu Serif", 13, QFont.Bold))
        logo.setAlignment(Qt.AlignCenter)
        logo.setFixedHeight(72)
        logo.setStyleSheet(f"color: {GOLD}; background: {BG_DEEP}; padding: 12px 0;")
        layout.addWidget(logo)

        div = GoldDivider()
        layout.addWidget(div)

        # Recherche
        search = QLineEdit()
        search.setPlaceholderText("Rechercher…")
        search.setFixedHeight(34)
        search.setStyleSheet(f"""
            QLineEdit {{
                background: {BG_DEEP};
                color: {TEXT_MAIN};
                border: none;
                border-bottom: 1px solid {DIVIDER};
                padding: 0 12px;
                font-size: 11px;
            }}
            QLineEdit:focus {{ border-bottom: 1px solid {GOLD_DIM}; }}
        """)
        search.textChanged.connect(self._on_search)
        self._search = search
        layout.addWidget(search)

        layout.addSpacing(6)

        # Liste des personnages
        for name, data in CHARACTERS.items():
            btn = CharacterButton(name, data)
            btn.clicked.connect(lambda _, n=name: self._select_character(n))
            self._char_buttons[name] = btn
            layout.addWidget(btn)

        layout.addStretch()

        div2 = GoldDivider()
        layout.addWidget(div2)

        # Contrôles volume en bas
        vol_w = QWidget()
        vol_w.setFixedHeight(52)
        vol_w.setStyleSheet(f"background: {BG_PANEL};")
        vol_layout = QHBoxLayout(vol_w)
        vol_layout.setContentsMargins(12, 0, 12, 0)
        vol_layout.setSpacing(8)

        vol_icon = QLabel("🔊")
        vol_icon.setStyleSheet(f"color: {TEXT_DIM}; font-size: 13px; background: transparent;")
        vol_layout.addWidget(vol_icon)

        self._vol_slider = QSlider(Qt.Horizontal)
        self._vol_slider.setRange(0, 100)
        self._vol_slider.setValue(80)
        self._vol_slider.setStyleSheet(f"""
            QSlider::groove:horizontal {{ height: 3px; background: {DIVIDER}; border-radius: 1px; }}
            QSlider::handle:horizontal {{
                width: 12px; height: 12px; margin: -4px 0;
                background: {GOLD}; border-radius: 6px;
            }}
            QSlider::sub-page:horizontal {{ background: {GOLD}; border-radius: 1px; }}
        """)
        self._vol_slider.valueChanged.connect(self._on_volume)
        vol_layout.addWidget(self._vol_slider)

        self._vol_pct = QLabel("80%")
        self._vol_pct.setFixedWidth(30)
        self._vol_pct.setStyleSheet(f"color: {TEXT_DIM}; font-size: 10px; background: transparent;")
        vol_layout.addWidget(self._vol_pct)

        layout.addWidget(vol_w)
        return sidebar

    def _build_topbar(self) -> QWidget:
        bar = QWidget()
        bar.setFixedHeight(52)
        bar.setStyleSheet(f"background: {BG_DEEP}; border-bottom: 1px solid {DIVIDER};")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(24, 0, 24, 0)
        layout.setSpacing(12)

        self._title_lbl = QLabel("Gimli")
        self._title_lbl.setFont(QFont("DejaVu Serif", 15, QFont.Bold))
        self._title_lbl.setStyleSheet(f"color: {GOLD_BRIGHT}; background: transparent;")
        layout.addWidget(self._title_lbl)

        layout.addStretch()

        stop_btn = QPushButton("⏹  Stop")
        stop_btn.setFixedSize(82, 32)
        stop_btn.setCursor(QCursor(Qt.PointingHandCursor))
        stop_btn.setToolTip("Arrêter (Échap)")
        stop_btn.setStyleSheet("""
            QPushButton {
                background: #3A0808;
                color: #FF8080;
                border: 1px solid #6A1010;
                border-radius: 6px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover { background: #6A1010; color: #FFFFFF; border-color: #AA2020; }
            QPushButton:pressed { background: #AA0000; }
        """)
        stop_btn.clicked.connect(self._stop)
        layout.addWidget(stop_btn)
        return bar

    def _build_nowplaying(self) -> QWidget:
        bar = QWidget()
        bar.setFixedHeight(40)
        bar.setStyleSheet(f"background: {BG_PANEL}; border-bottom: 1px solid {DIVIDER};")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(24, 0, 24, 0)
        layout.setSpacing(16)

        tag = QLabel("EN COURS")
        tag.setFont(QFont("DejaVu Sans", 7, QFont.Bold))
        tag.setStyleSheet(f"color: {TEXT_DIM}; background: transparent; letter-spacing: 2px;")
        layout.addWidget(tag)

        self._now_playing = PulseLabel("—")
        self._now_playing.setFont(QFont("DejaVu Serif", 10))
        layout.addWidget(self._now_playing, 1)

        self._progress = QProgressBar()
        self._progress.setRange(0, 100)
        self._progress.setValue(0)
        self._progress.setTextVisible(False)
        self._progress.setFixedSize(180, 4)
        self._progress.setStyleSheet(f"""
            QProgressBar {{
                background: {DIVIDER}; border-radius: 2px; border: none;
            }}
            QProgressBar::chunk {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 {GOLD_DIM}, stop:1 {GOLD_BRIGHT});
                border-radius: 2px;
            }}
        """)
        layout.addWidget(self._progress)
        return bar

    def _build_panel_stack(self) -> QWidget:
        self._stack = QWidget()
        self._stack.setStyleSheet(f"background: {BG_DEEP};")
        stack_layout = QVBoxLayout(self._stack)
        stack_layout.setContentsMargins(0, 0, 0, 0)

        for name, data in CHARACTERS.items():
            panel = CharacterPanel(name, data)
            panel.play_sound.connect(self._play)
            panel.setVisible(False)
            stack_layout.addWidget(panel)
            self._panels[name] = panel

        return self._stack

    # ── navigation ─────────────────────────────────────────────────────────

    def _select_character(self, name: str) -> None:
        for n, btn in self._char_buttons.items():
            btn.set_selected(n == name)
        for n, panel in self._panels.items():
            panel.setVisible(n == name)
        self._active_char = name
        self._title_lbl.setText(name)
        self._panels[name].install_shortcuts(self)
        self.status.showMessage(
            f"{CHARACTERS[name]['tag']} — {len(CHARACTERS[name]['sounds'])} répliques"
        )

    def _on_search(self, text: str) -> None:
        for panel in self._panels.values():
            panel.filter(text)

    def _setup_shortcuts(self) -> None:
        for key in (Qt.Key_Escape, Qt.Key_Space):
            QShortcut(QKeySequence(key), self).activated.connect(self._stop)

    def _apply_theme(self) -> None:
        pal = QPalette()
        pal.setColor(QPalette.Window, QColor(BG_DEEP))
        pal.setColor(QPalette.WindowText, QColor(TEXT_MAIN))
        pal.setColor(QPalette.Base, QColor(BG_PANEL))
        pal.setColor(QPalette.Text, QColor(TEXT_MAIN))
        pal.setColor(QPalette.Button, QColor(BG_CARD))
        pal.setColor(QPalette.ButtonText, QColor(TEXT_MAIN))
        pal.setColor(QPalette.Highlight, QColor(GOLD))
        pal.setColor(QPalette.HighlightedText, QColor(BG_DEEP))
        self.setPalette(pal)

    def closeEvent(self, event) -> None:
        pygame.mixer.stop()
        pygame.mixer.quit()
        event.accept()


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("LOTR Soundboard VF")
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
