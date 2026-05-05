#!/usr/bin/env python3
"""Soundboard Le Seigneur des Anneaux — version française."""

import os
import sys

os.environ.setdefault("SDL_AUDIODRIVER", "pulse,alsa,dummy")
os.environ.setdefault("SDL_VIDEODRIVER", "x11,wayland,offscreen")

import pygame
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QPushButton, QLabel, QSlider, QTabWidget,
    QScrollArea, QSizePolicy, QFrame, QStatusBar,
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QColor, QPalette, QIcon


SOUNDS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sounds")

CHARACTERS = {
    "Gimli": {
        "emoji": "⚒️",
        "color": "#8B4513",
        "accent": "#D2691E",
        "text_color": "#FFD700",
        "sounds": [
            ("et_ma_hache",              "« Et ma hache ! »"),
            ("personne_ne_jette_un_nain", "« Personne ne jette un nain ! »"),
            ("gloire_a_la_moria",         "« Gloire à la Moria ! »"),
            ("aucune_honte_davoir_peur",  "« Je n'ai aucune honte d'avoir peur ! »"),
            ("que_ca_serve_de_lecon",     "« Que ça serve de leçon ! »"),
            ("ma_langue_sur_des_marches_glacees", "« Ma langue sur des marches glacées... »"),
        ],
    },
    "Gandalf": {
        "emoji": "🧙",
        "color": "#2F4F4F",
        "accent": "#708090",
        "text_color": "#FFFFFF",
        "sounds": [
            ("vous_ne_passerez_pas",               "« Vous ne passerez pas ! »"),
            ("tu_ne_peux_pas_passer",              "« Tu ne peux pas passer ! »"),
            ("fuyez_pauvres_fous",                 "« Fuyez, pauvres fous ! »"),
            ("je_suis_gandalf_le_blanc",            "« Je suis Gandalf le Blanc ! »"),
            ("arrive_precisement_quand_il_le_decide", "« Un magicien arrive précisément quand il le décide »"),
        ],
    },
    "Aragorn": {
        "emoji": "⚔️",
        "color": "#1C1C1C",
        "accent": "#4A4A4A",
        "text_color": "#C0C0C0",
        "sounds": [
            ("ce_jour_nest_pas_encore_venu", "« Ce jour n'est pas encore venu ! »"),
            ("pour_frodon",                  "« Pour Frodon ! »"),
            ("mourons_ensemble",             "« Alors, mourons ensemble ! »"),
            ("pas_encore_vivants",           "« Ils ne sont pas encore vivants ! »"),
            ("roi_elessar",                  "« Roi Elessar ! »"),
        ],
    },
    "Legolas": {
        "emoji": "🏹",
        "color": "#2E5902",
        "accent": "#4B8B00",
        "text_color": "#E8FFD0",
        "sounds": [
            ("ils_vont_a_isengard",    "« Ils vont à Isengard ! »"),
            ("soixante_dix_fleches",   "« J'avais soixante-dix flèches ! »"),
            ("mon_arc_est_pret",       "« Mon arc est prêt ! »"),
            ("trois_jours_sans_dormir","« Trois jours sans dormir... »"),
        ],
    },
    "Frodon": {
        "emoji": "💍",
        "color": "#4B3A2A",
        "accent": "#7A5C3A",
        "text_color": "#FFE8C0",
        "sounds": [
            ("je_prends_lanneau",            "« Je prends l'Anneau ! »"),
            ("je_voudrais_que_cette_nuit",   "« Je voudrais que cette nuit n'ait jamais commencé »"),
            ("porteur_de_lanneau",           "« Porteur de l'Anneau »"),
            ("je_suis_heureux_que_tu_sois_la","« Je suis heureux que tu sois là, Sam »"),
        ],
    },
    "Sam": {
        "emoji": "🌻",
        "color": "#5C4A00",
        "accent": "#8B7000",
        "text_color": "#FFF5CC",
        "sounds": [
            ("je_peux_vous_porter",        "« Je ne peux pas porter l'Anneau... mais je peux vous porter ! »"),
            ("la_lumiere_le_sera_toujours","« La lumière le sera toujours »"),
            ("monsieur_frodon",            "« Monsieur Frodon ! »"),
            ("taters_les_pommes_de_terre", "« Les taters ! Les pommes de terre ! »"),
        ],
    },
    "Gollum": {
        "emoji": "👁️",
        "color": "#1A2A0A",
        "accent": "#2A3A1A",
        "text_color": "#AAFFAA",
        "sounds": [
            ("mon_precieux",           "« Mon Précieux ! »"),
            ("nous_voulons_ca",        "« Nous voulons ça, on veut... »"),
            ("nous_haissons_baggins",  "« Nous haïssons Baggins ! »"),
            ("pas_de_lembas_pour_nous","« Pas de lembas pour nous ! »"),
        ],
    },
    "Saruman": {
        "emoji": "🔮",
        "color": "#3A003A",
        "accent": "#600060",
        "text_color": "#FFB0FF",
        "sounds": [
            ("la_terre_du_milieu_tombera", "« La Terre du Milieu tombera ! »"),
            ("ordre_des_istari",           "« L'Ordre des Istari »"),
            ("palantir",                   "« Le Palantír ne ment pas »"),
        ],
    },
}


class AudioThread(QThread):
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, path):
        super().__init__()
        self.path = path

    def run(self):
        try:
            pygame.mixer.music.load(self.path)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                self.msleep(50)
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))


class SoundButton(QPushButton):
    def __init__(self, label, path, accent_color, parent=None):
        super().__init__(label, parent)
        self.path = path
        self.accent = accent_color
        self._playing = False
        self._setup_style(False)
        self.setMinimumHeight(52)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        font = QFont("DejaVu Sans", 10)
        font.setItalic(True)
        self.setFont(font)
        self.setWordWrap(True)

    def _setup_style(self, playing):
        bg = self.accent if playing else "#333333"
        border = self.accent
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg};
                color: #FFFFFF;
                border: 2px solid {border};
                border-radius: 8px;
                padding: 8px 12px;
                text-align: left;
            }}
            QPushButton:hover {{
                background-color: {self.accent};
                border: 2px solid #FFFFFF;
            }}
            QPushButton:pressed {{
                background-color: #FFFFFF;
                color: #000000;
            }}
        """)

    def set_playing(self, playing):
        self._playing = playing
        self._setup_style(playing)


class CharacterTab(QWidget):
    play_sound = pyqtSignal(str, object)

    def __init__(self, name, data, parent=None):
        super().__init__(parent)
        self.name = name
        self.data = data
        self.buttons = {}
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(16, 16, 16, 16)

        header = QLabel(f"{self.data['emoji']}  {self.name}")
        header.setFont(QFont("DejaVu Serif", 18, QFont.Bold))
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet(f"""
            color: {self.data['text_color']};
            background-color: {self.data['accent']};
            border-radius: 10px;
            padding: 10px;
            margin-bottom: 8px;
        """)
        layout.addWidget(header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background: transparent;")

        grid_widget = QWidget()
        grid = QGridLayout(grid_widget)
        grid.setSpacing(10)

        for i, (key, label) in enumerate(self.data["sounds"]):
            path = os.path.join(SOUNDS_DIR, self.name.lower(), f"{key}.wav")
            btn = SoundButton(label, path, self.data["accent"])
            if not os.path.exists(path):
                btn.setEnabled(False)
                btn.setToolTip(f"Fichier manquant : {path}")
            btn.clicked.connect(lambda _, p=path, b=btn: self.play_sound.emit(p, b))
            self.buttons[key] = btn
            row, col = divmod(i, 2)
            grid.addWidget(btn, row, col)

        grid_widget.setLayout(grid)
        scroll.setWidget(grid_widget)
        layout.addWidget(scroll)

        missing = sum(
            1 for key, _ in self.data["sounds"]
            if not os.path.exists(os.path.join(SOUNDS_DIR, self.name.lower(), f"{key}.wav"))
        )
        if missing:
            info = QLabel(f"ℹ️  {missing} fichier(s) manquant(s) — placez vos .wav dans sounds/{self.name.lower()}/")
            info.setStyleSheet("color: #FFA500; font-size: 11px; padding: 4px;")
            layout.addWidget(info)

    def reset_buttons(self):
        for btn in self.buttons.values():
            btn.set_playing(False)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🧙 Soundboard — Le Seigneur des Anneaux VF")
        self.setMinimumSize(780, 520)
        self._current_thread = None
        self._current_button = None
        self._setup_audio()
        self._build_ui()
        self._apply_dark_theme()

    def _setup_audio(self):
        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=1, buffer=512)
        except Exception as e:
            print(f"[audio] init warning: {e}")

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Top bar
        top_bar = QWidget()
        top_bar.setFixedHeight(56)
        top_bar.setStyleSheet("background-color: #0D0D0D;")
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(16, 0, 16, 0)

        title = QLabel("⚔️  Le Seigneur des Anneaux — Soundboard VF")
        title.setFont(QFont("DejaVu Serif", 13, QFont.Bold))
        title.setStyleSheet("color: #C8A040;")
        top_layout.addWidget(title)
        top_layout.addStretch()

        stop_btn = QPushButton("⏹  Stop")
        stop_btn.setFixedSize(90, 34)
        stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #8B0000;
                color: white;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #CC0000; }
        """)
        stop_btn.clicked.connect(self._stop_sound)
        top_layout.addWidget(stop_btn)

        vol_label = QLabel("🔊")
        vol_label.setStyleSheet("color: #AAAAAA; font-size: 16px; margin-left: 12px;")
        top_layout.addWidget(vol_label)

        self.vol_slider = QSlider(Qt.Horizontal)
        self.vol_slider.setRange(0, 100)
        self.vol_slider.setValue(80)
        self.vol_slider.setFixedWidth(100)
        self.vol_slider.setStyleSheet("""
            QSlider::groove:horizontal { height: 4px; background: #555; border-radius: 2px; }
            QSlider::handle:horizontal { width: 14px; height: 14px; margin: -5px 0;
                                          background: #C8A040; border-radius: 7px; }
            QSlider::sub-page:horizontal { background: #C8A040; border-radius: 2px; }
        """)
        self.vol_slider.valueChanged.connect(self._on_volume_change)
        top_layout.addWidget(self.vol_slider)
        self._on_volume_change(80)

        main_layout.addWidget(top_bar)

        # Tabs
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: none; background: #1A1A1A; }
            QTabBar::tab {
                background: #111111;
                color: #AAAAAA;
                padding: 8px 16px;
                border: none;
                font-size: 13px;
                min-width: 80px;
            }
            QTabBar::tab:selected {
                background: #2A2A2A;
                color: #C8A040;
                border-bottom: 2px solid #C8A040;
            }
            QTabBar::tab:hover { background: #222222; color: #FFFFFF; }
        """)

        self.char_tabs = {}
        for name, data in CHARACTERS.items():
            tab = CharacterTab(name, data)
            tab.play_sound.connect(self._play_sound)
            tab.setStyleSheet(f"background-color: {data['color']};")
            self.tabs.addTab(tab, f"{data['emoji']} {name}")
            self.char_tabs[name] = tab

        main_layout.addWidget(self.tabs, 1)

        # Status bar
        self.status = QStatusBar()
        self.status.setStyleSheet("background: #0D0D0D; color: #888888; font-size: 11px;")
        self.setStatusBar(self.status)
        self.status.showMessage("Prêt — cliquez sur un personnage pour jouer un son")

    def _apply_dark_theme(self):
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor("#1A1A1A"))
        palette.setColor(QPalette.WindowText, QColor("#DDDDDD"))
        palette.setColor(QPalette.Base, QColor("#111111"))
        palette.setColor(QPalette.AlternateBase, QColor("#222222"))
        palette.setColor(QPalette.Text, QColor("#EEEEEE"))
        palette.setColor(QPalette.Button, QColor("#333333"))
        palette.setColor(QPalette.ButtonText, QColor("#EEEEEE"))
        self.setPalette(palette)

    def _on_volume_change(self, value):
        pygame.mixer.music.set_volume(value / 100)

    def _stop_sound(self):
        pygame.mixer.music.stop()
        if self._current_button:
            self._current_button.set_playing(False)
            self._current_button = None
        self.status.showMessage("Arrêté.")

    def _reset_all_buttons(self):
        for tab in self.char_tabs.values():
            tab.reset_buttons()

    def _play_sound(self, path, button):
        if not os.path.exists(path):
            self.status.showMessage(f"⚠️  Fichier introuvable : {path}")
            return

        self._stop_sound()
        self._reset_all_buttons()

        if self._current_thread and self._current_thread.isRunning():
            self._current_thread.quit()
            self._current_thread.wait(200)

        button.set_playing(True)
        self._current_button = button
        name = os.path.splitext(os.path.basename(path))[0].replace("_", " ")
        char = os.path.basename(os.path.dirname(path)).capitalize()
        self.status.showMessage(f"▶  {char}  —  {name}")

        self._current_thread = AudioThread(path)
        self._current_thread.finished.connect(self._on_sound_finished)
        self._current_thread.error.connect(self._on_sound_error)
        self._current_thread.start()

    def _on_sound_finished(self):
        if self._current_button:
            self._current_button.set_playing(False)
            self._current_button = None
        self.status.showMessage("Prêt")

    def _on_sound_error(self, msg):
        self.status.showMessage(f"⚠️  Erreur audio : {msg}")
        if self._current_button:
            self._current_button.set_playing(False)
            self._current_button = None

    def closeEvent(self, event):
        pygame.mixer.quit()
        event.accept()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("LOTR Soundboard VF")
    app.setStyle("Fusion")

    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
