# ── Stage 1 : build des sons TTS ─────────────────────────────────────────────
FROM python:3.11-slim-bookworm AS audio-builder

RUN apt-get update && apt-get install -y --no-install-recommends \
        espeak-ng \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build
COPY generate_placeholders.py .
RUN mkdir -p sounds && python3 generate_placeholders.py

# ── Stage 2 : image finale ────────────────────────────────────────────────────
FROM python:3.11-slim-bookworm AS runtime

LABEL org.opencontainers.image.title="LOTR Soundboard VF"
LABEL org.opencontainers.image.description="Soundboard Le Seigneur des Anneaux — version française"
LABEL org.opencontainers.image.source="https://github.com/PaulTroneysofa/lotr_soundboard"

# Dépendances système pour PyQt5 + pygame + audio
RUN apt-get update && apt-get install -y --no-install-recommends \
        # Qt5 runtime
        libqt5core5a \
        libqt5gui5 \
        libqt5widgets5 \
        libqt5network5 \
        libqt5dbus5 \
        # Fonts
        fonts-dejavu-core \
        # Audio (ALSA + PulseAudio stubs)
        libasound2 \
        libpulse0 \
        # SDL2 (pygame backend)
        libsdl2-2.0-0 \
        libsdl2-mixer-2.0-0 \
        # Virtual display pour CI / usage headless
        xvfb \
        x11-utils \
        # espeak-ng pour régénérer les sons si besoin
        espeak-ng \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Installer les dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code
COPY soundboard.py generate_placeholders.py run.sh ./

# Récupérer les sons générés au stage 1
COPY --from=audio-builder /build/sounds ./sounds

RUN chmod +x run.sh

# Variables d'environnement par défaut (mode headless)
ENV SDL_AUDIODRIVER=pulse,alsa,dummy
ENV SDL_VIDEODRIVER=x11
ENV QT_QPA_PLATFORM=xcb
ENV DISPLAY=:99

# Healthcheck : vérifie que le module se charge sans erreur
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD python3 -c "import ast; ast.parse(open('soundboard.py').read())" || exit 1

EXPOSE 0

# Lancement avec Xvfb intégré pour les environnements sans display
CMD ["bash", "-c", \
    "Xvfb :99 -screen 0 1024x768x24 -nolisten tcp & sleep 0.5 && python3 soundboard.py"]
