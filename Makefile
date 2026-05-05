.PHONY: run lint fmt typecheck test sounds docker-build docker-run docker-headless clean

PYTHON   := python3
IMAGE    := lotr-soundboard
COMPOSE  := docker compose

# ── Développement local ────────────────────────────────────────────────────────

run:
	$(PYTHON) soundboard.py

sounds:
	$(PYTHON) generate_placeholders.py

sounds-force:
	$(PYTHON) generate_placeholders.py --force

# ── Qualité du code ───────────────────────────────────────────────────────────

lint:
	ruff check soundboard.py generate_placeholders.py

fmt:
	ruff format soundboard.py generate_placeholders.py

fmt-check:
	ruff format --check soundboard.py generate_placeholders.py

typecheck:
	mypy soundboard.py generate_placeholders.py

test: lint fmt-check typecheck
	@echo "--- Syntax check ---"
	$(PYTHON) -c "import ast; ast.parse(open('soundboard.py').read()); print('OK')"
	@echo "--- WAV validation ---"
	$(PYTHON) - <<'EOF'
	import wave, os, sys
	errors = []
	total = 0
	for char in os.listdir("sounds"):
	    d = os.path.join("sounds", char)
	    if not os.path.isdir(d): continue
	    for f in os.listdir(d):
	        if not f.endswith(".wav"): continue
	        with wave.open(os.path.join(d, f)) as w:
	            assert w.getnchannels() == 2, f"not stereo: {char}/{f}"
	            assert w.getframerate() == 44100, f"not 44100Hz: {char}/{f}"
	        total += 1
	print(f"OK: {total} WAV files valid")
	EOF
	@echo "All checks passed."

# ── Docker ────────────────────────────────────────────────────────────────────

docker-build:
	docker build --target runtime -t $(IMAGE):latest .

docker-build-audio:
	docker build --target audio-builder -t $(IMAGE)-builder:latest .

docker-run:
	$(COMPOSE) up soundboard

docker-headless:
	$(COMPOSE) --profile ci up soundboard-headless

docker-generate-sounds:
	$(COMPOSE) --profile tools run --rm generate-sounds

docker-push:
	docker push $(IMAGE):latest

docker-shell:
	docker run --rm -it \
	  -e SDL_AUDIODRIVER=dummy \
	  -e QT_QPA_PLATFORM=offscreen \
	  $(IMAGE):latest bash

# ── Nettoyage ─────────────────────────────────────────────────────────────────

clean:
	find . -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .mypy_cache .ruff_cache

clean-sounds:
	rm -f sounds/*/*.wav

docker-clean:
	$(COMPOSE) down --rmi local --volumes
	docker image rm $(IMAGE):latest $(IMAGE)-builder:latest 2>/dev/null || true
