"""Generates placeholder WAV beep files for each soundboard button."""
import wave
import struct
import math
import os

SAMPLE_RATE = 44100
DURATION = 0.4
VOLUME = 0.3


def make_beep(filename, freq, duration=DURATION):
    n_samples = int(SAMPLE_RATE * duration)
    with wave.open(filename, "w") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(SAMPLE_RATE)
        for i in range(n_samples):
            t = i / SAMPLE_RATE
            envelope = math.sin(math.pi * t / duration) ** 0.5
            sample = int(32767 * VOLUME * envelope * math.sin(2 * math.pi * freq * t))
            f.writeframes(struct.pack("<h", sample))


SOUNDS = {
    "gimli": [
        ("et_ma_hache", 220),
        ("personne_ne_jette_un_nain", 240),
        ("gloire_a_la_moria", 260),
        ("aucune_honte_davoir_peur", 280),
        ("que_ca_serve_de_lecon", 300),
        ("ma_langue_sur_des_marches_glacees", 320),
    ],
    "aragorn": [
        ("ce_jour_nest_pas_encore_venu", 330),
        ("pour_frodon", 350),
        ("mourons_ensemble", 370),
        ("pas_encore_vivants", 390),
        ("roi_elessar", 410),
    ],
    "gandalf": [
        ("vous_ne_passerez_pas", 440),
        ("fuyez_pauvres_fous", 460),
        ("je_suis_gandalf_le_blanc", 480),
        ("arrive_precisement_quand_il_le_decide", 500),
        ("tu_ne_peux_pas_passer", 520),
    ],
    "legolas": [
        ("ils_vont_a_isengard", 550),
        ("soixante_dix_fleches", 570),
        ("mon_arc_est_pret", 590),
        ("trois_jours_sans_dormir", 610),
    ],
    "frodon": [
        ("je_prends_lanneau", 630),
        ("je_voudrais_que_cette_nuit", 640),
        ("porteur_de_lanneau", 650),
        ("je_suis_heureux_que_tu_sois_la", 660),
    ],
    "sam": [
        ("je_peux_vous_porter", 680),
        ("la_lumiere_le_sera_toujours", 700),
        ("monsieur_frodon", 720),
        ("taters_les_pommes_de_terre", 740),
    ],
    "gollum": [
        ("mon_precieux", 760),
        ("nous_voulons_ca", 780),
        ("nous_haissons_baggins", 800),
        ("pas_de_lembas_pour_nous", 820),
    ],
    "saruman": [
        ("la_terre_du_milieu_tombera", 850),
        ("ordre_des_istari", 870),
        ("palantir", 890),
    ],
}

if __name__ == "__main__":
    base = os.path.join(os.path.dirname(__file__), "sounds")
    for character, clips in SOUNDS.items():
        char_dir = os.path.join(base, character)
        os.makedirs(char_dir, exist_ok=True)
        for name, freq in clips:
            path = os.path.join(char_dir, f"{name}.wav")
            if not os.path.exists(path):
                make_beep(path, freq)
                print(f"  created: {character}/{name}.wav")
    print("Done.")
