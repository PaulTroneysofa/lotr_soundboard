"""
Génère les fichiers audio pour le soundboard LOTR VF.

Priorité :
  1. espeak-ng (TTS français, installé automatiquement si possible)
  2. Motifs musicaux synthétiques (fallback sans dépendances)

Usage : python3 generate_placeholders.py [--force]
  --force  : régénère même si les fichiers existent déjà
"""
import math
import os
import shutil
import struct
import subprocess
import sys
import wave

SR = 44100

CLIPS = [
    # (character, filename, text_fr, speed, pitch)
    ("gimli",   "et_ma_hache",              "Et ma hache !",                          75, 30),
    ("gimli",   "personne_ne_jette_un_nain","Personne ne jette un nain !",            80, 28),
    ("gimli",   "gloire_a_la_moria",        "Gloire à la Moria !",                    78, 25),
    ("gimli",   "aucune_honte_davoir_peur", "Je n'ai aucune honte d'avoir peur !",    82, 30),
    ("gimli",   "que_ca_serve_de_lecon",    "Que ça serve de leçon !",                80, 28),
    ("gimli",   "ma_langue_sur_des_marches_glacees", "Ma langue sur des marches glacées.", 85, 30),

    ("gandalf", "vous_ne_passerez_pas",               "Vous ne passerez pas !",       70, 45),
    ("gandalf", "tu_ne_peux_pas_passer",              "Tu ne peux pas passer !",       72, 43),
    ("gandalf", "fuyez_pauvres_fous",                 "Fuyez, pauvres fous !",         78, 50),
    ("gandalf", "je_suis_gandalf_le_blanc",            "Je suis Gandalf le Blanc !",   75, 52),
    ("gandalf", "arrive_precisement_quand_il_le_decide",
     "Un magicien arrive précisément quand il le décide.",                             80, 55),

    ("aragorn", "ce_jour_nest_pas_encore_venu", "Ce jour n'est pas encore venu !",    78, 40),
    ("aragorn", "pour_frodon",                  "Pour Frodon !",                       72, 42),
    ("aragorn", "mourons_ensemble",             "Alors, mourons ensemble !",           75, 38),
    ("aragorn", "pas_encore_vivants",           "Ils ne sont pas encore vivants !",    80, 40),
    ("aragorn", "roi_elessar",                  "Roi Elessar !",                       72, 45),

    ("legolas", "ils_vont_a_isengard",    "Ils vont à Isengard !",                    90, 60),
    ("legolas", "soixante_dix_fleches",   "J'avais soixante-dix flèches !",           88, 58),
    ("legolas", "mon_arc_est_pret",       "Mon arc est prêt !",                       92, 62),
    ("legolas", "trois_jours_sans_dormir","Trois jours sans dormir.",                 85, 58),

    ("frodon",  "je_prends_lanneau",             "Je prends l'Anneau.",               85, 55),
    ("frodon",  "je_voudrais_que_cette_nuit",    "Je voudrais que cette nuit n'ait jamais commencé.", 80, 52),
    ("frodon",  "porteur_de_lanneau",            "Porteur de l'Anneau.",              82, 53),
    ("frodon",  "je_suis_heureux_que_tu_sois_la","Je suis heureux que tu sois là, Sam.", 83, 55),

    ("sam",     "je_peux_vous_porter",        "Je ne peux pas porter l'Anneau, mais je peux vous porter !", 80, 50),
    ("sam",     "la_lumiere_le_sera_toujours","La lumière le sera toujours.",         82, 52),
    ("sam",     "monsieur_frodon",            "Monsieur Frodon !",                    85, 50),
    ("sam",     "taters_les_pommes_de_terre", "Les taters ! Les pommes de terre !",  90, 52),

    ("gollum",  "mon_precieux",           "Mon Précieux !",                           70, 70),
    ("gollum",  "nous_voulons_ca",        "Nous voulons ça, on veut.",               68, 72),
    ("gollum",  "nous_haissons_baggins",  "Nous haïssons Baggins !",                 72, 68),
    ("gollum",  "pas_de_lembas_pour_nous","Pas de lembas pour nous !",               70, 70),

    ("saruman", "la_terre_du_milieu_tombera", "La Terre du Milieu tombera !",        68, 20),
    ("saruman", "ordre_des_istari",           "L'Ordre des Istari.",                  70, 18),
    ("saruman", "palantir",                   "Le Palantír ne ment pas.",             72, 22),
]


def _note(freq, dur, vol=0.32):
    n = int(SR * dur)
    frames = []
    for i in range(n):
        t = i / SR
        env = math.sin(math.pi * t / dur) ** 0.4
        v = int(32767 * vol * env * (math.sin(2 * math.pi * freq * t)
                                     + 0.3 * math.sin(4 * math.pi * freq * t)))
        v = max(-32767, min(32767, v))
        frames.append(v)
    return frames


def _chord(freqs, dur, vol=0.22):
    n = int(SR * dur)
    frames = []
    for i in range(n):
        t = i / SR
        env = math.sin(math.pi * t / dur) ** 0.4
        s = sum(math.sin(2 * math.pi * f * t) for f in freqs)
        v = int(32767 * vol * env * s / len(freqs))
        v = max(-32767, min(32767, v))
        frames.append(v)
    return frames


def _silence(dur):
    return [0] * int(SR * dur)


# Fallback musical motifs (character → list of sample arrays)
_MOTIFS: dict[str, list] = {
    "gimli":   _note(130, 0.2) + _note(164, 0.2) + _chord([110, 196, 261], 0.5),
    "gandalf": _note(392, 0.2) + _note(440, 0.2) + _chord([261, 329, 392, 523], 0.6),
    "aragorn": _note(293, 0.2) + _note(440, 0.2) + _chord([293, 369, 440], 0.55),
    "legolas": _note(523, 0.1) + _note(587, 0.1) + _note(659, 0.1) + _chord([440, 659, 784], 0.4),
    "frodon":  _note(261, 0.2) + _note(329, 0.2) + _chord([261, 329, 392], 0.55),
    "sam":     _note(392, 0.2) + _note(440, 0.2) + _chord([261, 329, 392, 523], 0.5),
    "gollum":  _note(293, 0.2) + _note(int(293 * 1.06), 0.2) + _chord([220, int(330*1.05), int(440*0.97)], 0.55),
    "saruman": _note(110, 0.25) + _chord([98, 147, 196], 0.65),
}


def _save_stereo(path: str, samples: list[int]) -> None:
    with wave.open(path, "w") as f:
        f.setnchannels(2)
        f.setsampwidth(2)
        f.setframerate(SR)
        for s in samples:
            f.writeframes(struct.pack("<hh", s, s))


def _convert_to_stereo_44100(mono_22050_path: str) -> None:
    with wave.open(mono_22050_path, "rb") as r:
        sw, sr = r.getsampwidth(), r.getframerate()
        raw = r.readframes(r.getnframes())

    n = len(raw) // sw
    samples = list(struct.unpack(f"<{n}h", raw))

    # Upsample if needed
    ratio = SR / sr
    if ratio != 1.0:
        out_n = int(n * ratio)
        ups = []
        for i in range(out_n):
            src = i / ratio
            i0 = int(src)
            i1 = min(i0 + 1, n - 1)
            ups.append(int(samples[i0] * (1 - src + i0) + samples[i1] * (src - i0)))
        samples = ups

    _save_stereo(mono_22050_path, samples)


def generate_espeak(base: str, force: bool) -> bool:
    """Try to generate all clips with espeak-ng. Returns True on full success."""
    espeak = shutil.which("espeak-ng")
    if not espeak:
        return False

    ok, err = 0, 0
    for char, name, text, speed, pitch in CLIPS:
        out = os.path.join(base, char, f"{name}.wav")
        os.makedirs(os.path.dirname(out), exist_ok=True)
        if os.path.exists(out) and not force:
            ok += 1
            continue
        res = subprocess.run(
            [espeak, "-v", "fr-fr", "-s", str(speed), "-p", str(pitch),
             "-a", "180", "-w", out, text],
            capture_output=True,
        )
        if res.returncode == 0 and os.path.exists(out) and os.path.getsize(out) > 100:
            _convert_to_stereo_44100(out)
            print(f"  TTS  {char}/{name}")
            ok += 1
        else:
            print(f"  ERR  {char}/{name}")
            err += 1

    print(f"espeak-ng : {ok} OK, {err} erreurs")
    return err == 0


def generate_synthetic(base: str, force: bool) -> None:
    """Fallback: generate musical beep motifs."""
    for char, name, *_ in CLIPS:
        out = os.path.join(base, char, f"{name}.wav")
        os.makedirs(os.path.dirname(out), exist_ok=True)
        if os.path.exists(out) and not force:
            continue
        motif = _MOTIFS.get(char, _note(440, 0.4))
        _save_stereo(out, motif)
        print(f"  SYN  {char}/{name}")


if __name__ == "__main__":
    force = "--force" in sys.argv
    base = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sounds")

    if not generate_espeak(base, force):
        print("espeak-ng indisponible — génération synthétique…")
        generate_synthetic(base, force)

    print("Terminé.")
