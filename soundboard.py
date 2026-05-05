#!/usr/bin/env python3
"""Soundboard Le Seigneur des Anneaux — version française."""

import os
import sys
import time

os.environ.setdefault("SDL_AUDIODRIVER", "pulse,alsa,dummy")
os.environ.setdefault("SDL_VIDEODRIVER", "x11,wayland,offscreen")

import pygame
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QPushButton, QLabel, QSlider, QTabWidget,
    QScrollArea, QSizePolicy, QFrame, QStatusBar, QProgressBar,
    QLineEdit, QShortcut,
)
from PyQt5.QtCore import (
    Qt, QThread, pyqtSignal, QPropertyAnimation,
    QEasingCurve, QPoint, QRect, pyqtProperty,
)
from PyQt5.QtGui import QFont, QColor, QPalette, QKeySequence


SOUNDS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sounds")

CHARACTERS = {
    "Gimli": {
        "emoji": "⚒️",
        "color": "#4A2010",
        "accent": "#C05820",
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
        "color": "#1A2A2A",
        "accent": "#5A7A8A",
        "text_color": "#EEEEFF",
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
        "color": "#1A1E2A",
        "accent": "#3A5080",
        "text_color": "#C8D8FF",
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
        "color": "#0E2A10",
        "accent": "#3A8040",
        "text_color": "#D0FFD8",
        "sounds": [
            ("ils_vont_a_isengard",    "« Ils vont à Isengard ! »"),
            ("soixante_dix_fleches",   "« J'avais soixante-dix flèches ! »"),
            ("mon_arc_est_pret",       "« Mon arc est prêt ! »"),
            ("trois_jours_sans_dormir","« Trois jours sans dormir... »"),
        ],
    },
    "Frodon": {
        "emoji": "💍",
        "color": "#2A1E10",
        "accent": "#6A4820",
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
        "color": "#2A2000",
        "accent": "#7A6010",
        "text_color": "#FFF5AA",
        "sounds": [
            ("je_peux_vous_porter",        "« Je ne peux pas porter l'Anneau... mais je peux vous porter ! »"),
            ("la_lumiere_le_sera_toujours","« La lumière le sera toujours »"),
            ("monsieur_frodon",            "« Monsieur Frodon ! »"),
            ("taters_les_pommes_de_terre", "« Les taters ! Les pommes de terre ! »"),
        ],
    },
    "Gollum": {
        "emoji": "👁️",
        "color": "#080F05",
        "accent": "#1E3A10",
        "text_color": "#88FF88",
        "sounds": [
            ("mon_precieux",           "« Mon Précieux ! »"),
            ("nous_voulons_ca",        "« Nous voulons ça, on veut... »"),
            ("nous_haissons_baggins",  "« Nous haïssons Baggins ! »"),
            ("pas_de_lembas_pour_nous","« Pas de lembas pour nous ! »"),
        ],
    },
    "Saruman": {
        "emoji": "🔮",
        "color": "#200030",
        "accent": "#700090",
        "text_color": "#FFCCFF",
        "sounds": [
            ("la_terre_du_milieu_tombera", "« La Terre du Milieu tombera ! »"),
            ("ordre_des_istari",           "« L'Ordre des Istari »"),
            ("palantir",                   "« Le Palantír ne ment pas »"),
        ],
    },
}


class AudioThread(QThread):
    finished = pyqtSignal(int)   # carries generation id to detect stale signals
    error = pyqtSignal(str, int)
    progress = pyqtSignal(float) # 0.0–1.0

    def __init__(self, path, gen_id, volume):
        super().__init__()
        self.path = path
        self.gen_id = gen_id
        self._volume = volume

    def run(self):
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


class PulseLabel(QLabel):
    """QLabel that animates opacity to create a pulsing 'now playing' effect."""

    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self._opacity = 1.0
        self._anim = QPropertyAnimation(self, b"opacity_prop")
        self._anim.setDuration(900)
        self._anim.setStartValue(1.0)
        self._anim.setEndValue(0.3)
        self._anim.setEasingCurve(QEasingCurve.InOutSine)
        self._anim.setLoopCount(-1)  # infinite
        self._anim.finished.connect(self._toggle_direction)

    def _toggle_direction(self):
        pass  # handled by loop

    def start_pulse(self):
        self._anim.stop()
        self._anim.setDirection(QPropertyAnimation.Forward)
        self._anim.start()

    def stop_pulse(self):
        self._anim.stop()
        self._set_opacity(1.0)

    @pyqtProperty(float)
    def opacity_prop(self):
        return self._opacity

    @opacity_prop.setter
    def opacity_prop(self, value):
        self._set_opacity(value)

    def _set_opacity(self, value):
        self._opacity = value
        self.setStyleSheet(
            self.styleSheet().split("opacity")[0]
            + f"; color: rgba(200,160,64,{int(value*255)});"
        )


class SoundButton(QPushButton):
    def __init__(self, label, path, accent_color, index, parent=None):
        super().__init__(parent)
        self.path = path
        self.accent = accent_color
        self.index = index
        self._playing = False

        display = f"[{index + 1}]  {label}" if index < 9 else label
        self.setText(display)
        self.setMinimumHeight(58)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        font = QFont("DejaVu Sans", 10)
        font.setItalic(True)
        self.setFont(font)
        self.setWordWrap(True)
        self._apply_style(False)

    def _apply_style(self, playing):
        if playing:
            bg = self.accent
            border = "#FFFFFF"
            glow = f"border: 2px solid #FFFFFF; background-color: {self.accent};"
        else:
            bg = "#2A2A2A"
            border = self.accent
            glow = ""
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg};
                color: #F0F0F0;
                border: 2px solid {border};
                border-radius: 8px;
                padding: 10px 14px;
                text-align: left;
            }}
            QPushButton:hover {{
                background-color: {self.accent};
                border: 2px solid #FFFFFF;
                color: #FFFFFF;
            }}
            QPushButton:pressed {{
                background-color: #FFFFFF;
                color: #111111;
            }}
            QPushButton:disabled {{
                background-color: #1A1A1A;
                border: 1px solid #333333;
                color: #555555;
            }}
        """)

    def set_playing(self, playing):
        if self._playing == playing:
            return
        self._playing = playing
        self._apply_style(playing)


class CharacterTab(QWidget):
    play_sound = pyqtSignal(str, object)

    def __init__(self, name, data, parent=None):
        super().__init__(parent)
        self.name = name
        self.data = data
        self.buttons: dict[str, SoundButton] = {}
        self._shortcuts = []
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(16, 16, 16, 16)

        header = QLabel(f"{self.data['emoji']}  {self.name}")
        header.setFont(QFont("DejaVu Serif", 20, QFont.Bold))
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet(f"""
            color: {self.data['text_color']};
            background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                stop:0 {self.data['color']}, stop:0.5 {self.data['accent']}, stop:1 {self.data['color']});
            border-radius: 10px;
            padding: 12px;
        """)
        layout.addWidget(header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background: transparent; border: none;")

        grid_widget = QWidget()
        grid_widget.setStyleSheet("background: transparent;")
        grid = QGridLayout(grid_widget)
        grid.setSpacing(10)
        grid.setContentsMargins(0, 0, 0, 0)

        for i, (key, label) in enumerate(self.data["sounds"]):
            path = os.path.join(SOUNDS_DIR, self.name.lower(), f"{key}.wav")
            btn = SoundButton(label, path, self.data["accent"], i)
            if not os.path.exists(path):
                btn.setEnabled(False)
                btn.setToolTip(f"Fichier manquant :\n{path}")
            else:
                btn.clicked.connect(lambda _, p=path, b=btn: self.play_sound.emit(p, b))
            self.buttons[key] = btn
            row, col = divmod(i, 2)
            grid.addWidget(btn, row, col)

        scroll.setWidget(grid_widget)
        layout.addWidget(scroll, 1)

        missing = sum(
            1 for key, _ in self.data["sounds"]
            if not os.path.exists(os.path.join(SOUNDS_DIR, self.name.lower(), f"{key}.wav"))
        )
        if missing:
            warn = QLabel(f"⚠  {missing} fichier(s) audio manquant(s) — "
                          f"déposez vos .wav dans sounds/{self.name.lower()}/")
            warn.setStyleSheet(
                "color: #FFA040; font-size: 11px; padding: 6px; "
                "background: #1A1000; border-radius: 4px;"
            )
            layout.addWidget(warn)

    def install_shortcuts(self, window):
        """Attach number key shortcuts 1–9 to buttons (active for this tab)."""
        for sc in self._shortcuts:
            sc.setEnabled(False)
        self._shortcuts.clear()
        for i, btn in enumerate(self.buttons.values()):
            if i >= 9 or not btn.isEnabled():
                continue
            sc = QShortcut(QKeySequence(str(i + 1)), window)
            sc.activated.connect(btn.click)
            self._shortcuts.append(sc)

    def reset_buttons(self):
        for btn in self.buttons.values():
            btn.set_playing(False)

    def filter(self, text: str):
        text = text.lower()
        for btn in self.buttons.values():
            visible = not text or text in btn.text().lower()
            btn.setVisible(visible)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Le Seigneur des Anneaux — Soundboard VF")
        self.setMinimumSize(860, 580)
        self._gen_id = 0
        self._current_thread: AudioThread | None = None
        self._current_button: SoundButton | None = None
        self._volume = 0.80
        self._setup_audio()
        self._build_ui()
        self._apply_theme()
        self._setup_global_shortcuts()

    # ------------------------------------------------------------------ audio

    def _setup_audio(self):
        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)
            pygame.mixer.set_num_channels(8)
        except Exception as e:
            print(f"[audio] init warning: {e}")

    def _stop_sound(self):
        pygame.mixer.stop()
        if self._current_button:
            self._current_button.set_playing(False)
            self._current_button = None
        self._gen_id += 1  # invalidate any running thread's signals
        self._progress.setValue(0)
        self._now_playing.setText("—")
        self._now_playing.stop_pulse()
        self.status.showMessage("Arrêté")

    def _play_sound(self, path: str, button: SoundButton):
        if not os.path.exists(path):
            self.status.showMessage(f"⚠  Fichier introuvable : {path}")
            return

        # Stop current + bump generation counter so stale signals are ignored
        pygame.mixer.stop()
        if self._current_button:
            self._current_button.set_playing(False)
        self._gen_id += 1
        gen = self._gen_id

        button.set_playing(True)
        self._current_button = button

        char = os.path.basename(os.path.dirname(path)).capitalize()
        label = button.text().split("]  ", 1)[-1]  # strip [N] prefix
        self._now_playing.setText(f"{CHARACTERS[char]['emoji']}  {label}")
        self._now_playing.start_pulse()
        self.status.showMessage(f"▶  {char}  —  {label}")
        self._progress.setValue(0)

        self._current_thread = AudioThread(path, gen, self._volume)
        self._current_thread.finished.connect(self._on_finished)
        self._current_thread.error.connect(self._on_error)
        self._current_thread.progress.connect(self._on_progress)
        self._current_thread.start()

    def _on_finished(self, gen_id: int):
        if gen_id != self._gen_id:
            return
        if self._current_button:
            self._current_button.set_playing(False)
            self._current_button = None
        self._progress.setValue(0)
        self._now_playing.setText("—")
        self._now_playing.stop_pulse()
        self.status.showMessage("Prêt")

    def _on_error(self, msg: str, gen_id: int):
        if gen_id != self._gen_id:
            return
        if self._current_button:
            self._current_button.set_playing(False)
            self._current_button = None
        self._now_playing.setText("—")
        self._now_playing.stop_pulse()
        self.status.showMessage(f"⚠  Erreur audio : {msg}")

    def _on_progress(self, ratio: float):
        self._progress.setValue(int(ratio * 100))

    def _on_volume_change(self, value: int):
        self._volume = value / 100
        self._vol_pct.setText(f"{value}%")

    # ------------------------------------------------------------------- UI

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._make_topbar())
        root.addWidget(self._make_nowplaying_bar())
        root.addWidget(self._make_tabs(), 1)

        self.status = QStatusBar()
        self.status.setStyleSheet(
            "background: #080808; color: #666666; font-size: 11px; padding: 2px 8px;"
        )
        self.setStatusBar(self.status)
        self.status.showMessage("Prêt — cliquez sur un personnage pour jouer un son")

    def _make_topbar(self):
        bar = QWidget()
        bar.setFixedHeight(58)
        bar.setStyleSheet("background: #080808; border-bottom: 1px solid #222;")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(12)

        title = QLabel("⚔️  Le Seigneur des Anneaux — Soundboard VF")
        title.setFont(QFont("DejaVu Serif", 13, QFont.Bold))
        title.setStyleSheet("color: #C8A040; background: transparent;")
        layout.addWidget(title)
        layout.addStretch()

        # Search
        self._search = QLineEdit()
        self._search.setPlaceholderText("🔍  Rechercher une réplique…")
        self._search.setFixedWidth(220)
        self._search.setStyleSheet("""
            QLineEdit {
                background: #1A1A1A;
                color: #DDDDDD;
                border: 1px solid #444;
                border-radius: 6px;
                padding: 4px 8px;
                font-size: 11px;
            }
            QLineEdit:focus { border-color: #C8A040; }
        """)
        self._search.textChanged.connect(self._on_search)
        layout.addWidget(self._search)

        stop_btn = QPushButton("⏹  Stop")
        stop_btn.setFixedSize(88, 34)
        stop_btn.setToolTip("Arrêter (Échap)")
        stop_btn.setStyleSheet("""
            QPushButton {
                background: #6B0000;
                color: #FFFFFF;
                border: 1px solid #AA0000;
                border-radius: 6px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover { background: #AA0000; }
            QPushButton:pressed { background: #DD0000; }
        """)
        stop_btn.clicked.connect(self._stop_sound)
        layout.addWidget(stop_btn)

        vol_icon = QLabel("🔊")
        vol_icon.setStyleSheet("color: #888; font-size: 15px; background: transparent;")
        layout.addWidget(vol_icon)

        self._vol_pct = QLabel("80%")
        self._vol_pct.setFixedWidth(34)
        self._vol_pct.setStyleSheet("color: #888; font-size: 11px; background: transparent;")
        layout.addWidget(self._vol_pct)

        self.vol_slider = QSlider(Qt.Horizontal)
        self.vol_slider.setRange(0, 100)
        self.vol_slider.setValue(80)
        self.vol_slider.setFixedWidth(110)
        self.vol_slider.setToolTip("Volume")
        self.vol_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                height: 4px; background: #333; border-radius: 2px;
            }
            QSlider::handle:horizontal {
                width: 14px; height: 14px; margin: -5px 0;
                background: #C8A040; border-radius: 7px;
            }
            QSlider::sub-page:horizontal { background: #C8A040; border-radius: 2px; }
        """)
        self.vol_slider.valueChanged.connect(self._on_volume_change)
        layout.addWidget(self.vol_slider)
        return bar

    def _make_nowplaying_bar(self):
        bar = QWidget()
        bar.setFixedHeight(38)
        bar.setStyleSheet("background: #0F0F0F; border-bottom: 1px solid #1A1A1A;")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(12)

        lbl = QLabel("En cours :")
        lbl.setStyleSheet("color: #555; font-size: 11px; background: transparent;")
        layout.addWidget(lbl)

        self._now_playing = PulseLabel("—")
        self._now_playing.setFont(QFont("DejaVu Serif", 11, QFont.Bold))
        self._now_playing.setStyleSheet(
            "color: #C8A040; background: transparent; font-style: italic;"
        )
        layout.addWidget(self._now_playing, 1)

        self._progress = QProgressBar()
        self._progress.setRange(0, 100)
        self._progress.setValue(0)
        self._progress.setTextVisible(False)
        self._progress.setFixedWidth(200)
        self._progress.setFixedHeight(6)
        self._progress.setStyleSheet("""
            QProgressBar {
                background: #222; border-radius: 3px; border: none;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #C8A040, stop:1 #FFD080);
                border-radius: 3px;
            }
        """)
        layout.addWidget(self._progress)
        return bar

    def _make_tabs(self):
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: none; }
            QTabBar::tab {
                background: #0D0D0D;
                color: #888888;
                padding: 9px 14px;
                border: none;
                border-right: 1px solid #1A1A1A;
                font-size: 12px;
                min-width: 88px;
            }
            QTabBar::tab:selected {
                background: #1A1A1A;
                color: #C8A040;
                border-bottom: 2px solid #C8A040;
            }
            QTabBar::tab:hover:!selected { background: #181818; color: #CCCCCC; }
            QTabBar { background: #0D0D0D; }
        """)

        self.char_tabs: dict[str, CharacterTab] = {}
        for name, data in CHARACTERS.items():
            tab = CharacterTab(name, data)
            tab.play_sound.connect(self._play_sound)
            tab.setStyleSheet(f"background-color: {data['color']};")
            self.tabs.addTab(tab, f"{data['emoji']} {name}")
            self.char_tabs[name] = tab

        self.tabs.currentChanged.connect(self._on_tab_changed)
        self._on_tab_changed(0)
        return self.tabs

    # ---------------------------------------------------------------- events

    def _setup_global_shortcuts(self):
        esc = QShortcut(QKeySequence(Qt.Key_Escape), self)
        esc.activated.connect(self._stop_sound)
        space = QShortcut(QKeySequence(Qt.Key_Space), self)
        space.activated.connect(self._stop_sound)

    def _on_tab_changed(self, index: int):
        name = list(CHARACTERS.keys())[index]
        tab = self.char_tabs[name]
        tab.install_shortcuts(self)

    def _on_search(self, text: str):
        for tab in self.char_tabs.values():
            tab.filter(text)

    def _apply_theme(self):
        palette = QPalette()
        dark = QColor("#111111")
        palette.setColor(QPalette.Window, dark)
        palette.setColor(QPalette.WindowText, QColor("#DDDDDD"))
        palette.setColor(QPalette.Base, dark)
        palette.setColor(QPalette.AlternateBase, QColor("#1A1A1A"))
        palette.setColor(QPalette.Text, QColor("#EEEEEE"))
        palette.setColor(QPalette.Button, QColor("#222222"))
        palette.setColor(QPalette.ButtonText, QColor("#EEEEEE"))
        palette.setColor(QPalette.Highlight, QColor("#C8A040"))
        palette.setColor(QPalette.HighlightedText, QColor("#111111"))
        self.setPalette(palette)

    def closeEvent(self, event):
        pygame.mixer.stop()
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
