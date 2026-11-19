# Grile Atestare

Site static cu grile pentru examenul de atestare MDLPA (expert tehnic A1).

- `questions_a1.json` — baza de întrebări (id, d = act normativ, q, o = variante, c = indexul răspunsului corect, e = explicație, r = temei legal)
- `assets/` — stil, scriptul aplicației de grile, fonturi (Source Serif 4, licență OFL)
- `build.py` — generează site-ul în `docs/`
- `config.json` (opțional) — suprascrie valorile din `CONFIG` (e-mail de contact, formular, analytics, operator)

Publicare: GitHub Pages, ramura `main`, folderul `/docs`, domeniu `grileatestare.ro`.

```
python3 build.py
```
