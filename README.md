# ⚔️ Soundboard — Le Seigneur des Anneaux VF

Soundboard Linux pour les répliques françaises du Seigneur des Anneaux.

## Personnages

| Personnage | Répliques incluses |
|---|---|
| ⚒️ Gimli | Et ma hache, Personne ne jette un nain, Gloire à la Moria... |
| 🧙 Gandalf | Vous ne passerez pas !, Fuyez pauvres fous !... |
| ⚔️ Aragorn | Ce jour n'est pas encore venu, Pour Frodon... |
| 🏹 Legolas | Ils vont à Isengard !, Soixante-dix flèches... |
| 💍 Frodon | Je prends l'Anneau, Porteur de l'Anneau... |
| 🌻 Sam | Je peux vous porter, La lumière le sera toujours... |
| 👁️ Gollum | Mon Précieux !, Nous haïssons Baggins !... |
| 🔮 Saruman | La Terre du Milieu tombera !... |

## Installation

```bash
pip3 install pygame PyQt5
python3 generate_placeholders.py  # génère des bips de test
```

## Lancement

```bash
./run.sh
# ou
python3 soundboard.py
```

## Ajouter vos propres sons

Placez vos fichiers `.wav` dans le dossier correspondant :

```
sounds/
├── gimli/
│   ├── et_ma_hache.wav
│   ├── personne_ne_jette_un_nain.wav
│   └── ...
├── gandalf/
│   ├── vous_ne_passerez_pas.wav
│   └── ...
└── ...
```

Les fichiers WAV remplacent automatiquement les bips placeholders au prochain lancement.

## Dépendances

- Python 3.8+
- `pygame` (audio)
- `PyQt5` (interface graphique)
