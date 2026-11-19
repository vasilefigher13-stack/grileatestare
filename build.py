#!/usr/bin/env python3
"""Generează site-ul static Grile Atestare în docs/.

Rulare:  python3 build.py
Configurarea (domeniu, e-mail, formular, analytics) se face în CONFIG de mai jos.
"""
import html
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "docs"  # GitHub Pages servește din /docs pe ramura main

CONFIG = {
    "name": "Grile Atestare",
    "domain": "grileatestare.ro",
    "updated_human": "19 noiembrie 2026",
    "updated_iso": "2026-11-19",
    "law_checked": "28 octombrie 2026",
    # Se completează după ce sunt create conturile:
    "contact_email": "",        # ex. contact@grileatestare.ro
    "waitlist_url": "",         # linkul formularului Google
    "cf_beacon_token": "",      # Cloudflare Web Analytics
    "google_verification": "",  # Google Search Console (meta tag)
    "operator": "",             # cine administrează datele (GDPR)
}
if (ROOT / "config.json").exists():
    CONFIG.update(json.loads((ROOT / "config.json").read_text()))
BASE = "https://" + CONFIG["domain"]

DOMAINS = {
    "catuc": {"label": "Legea nr. 169/2026", "slug": "legea-169-2026",
              "title": "Legea nr. 169/2026 – Codul amenajării teritoriului, urbanismului și construcțiilor",
              "short": "Legea nr. 169/2026 (noul Cod al construcțiilor)",
              "intro": "Legea nr. 169/2026 privind Codul amenajării teritoriului, urbanismului și construcțiilor a fost publicată în Monitorul Oficial nr. 661 din 10 august 2026, rectificată în Monitorul Oficial nr. 862 din 14 octombrie 2026, și se aplică din 25 august 2026. Întrebările acoperă ce contează pentru experți și verificatori: clasele de consecințe, nivelurile de verificare, expertiza tehnică, răspunderea și sancțiunile."},
    "proc": {"label": "Procedura de atestare", "slug": "procedura-atestare",
             "title": "Procedura de atestare a verificatorilor și experților (Ordinul MDLPA nr. 817/2021)",
             "short": "Procedura de atestare (Ordinul nr. 817/2021)",
             "intro": "Procedura privind atestarea tehnico-profesională a verificatorilor de proiecte și a experților tehnici, aprobată prin Ordinul MDLPA nr. 817/2021: condițiile de înscriere, desfășurarea examenului, notarea și contestațiile."},
    "hg925": {"label": "HG nr. 925/1995", "slug": "hg-925-1995",
              "title": "Regulamentul aprobat prin HG nr. 925/1995 – verificarea și expertizarea tehnică de calitate",
              "short": "Regulamentul aprobat prin HG nr. 925/1995",
              "intro": "Regulamentul de verificare și expertizare tehnică de calitate a proiectelor, a execuției lucrărilor și a construcțiilor, aprobat prin HG nr. 925/1995, rămâne în vigoare și după intrarea în vigoare a noului Cod, până la modificarea lui."},
    "p1001": {"label": "P100-1/2013", "slug": "p100-1-2013",
              "title": "P100-1/2013 – Cod de proiectare seismică, partea I",
              "short": "P100-1/2013",
              "intro": "Codul de proiectare seismică P100-1/2013, partea I – Prevederi de proiectare pentru clădiri: acțiunea seismică și spectrele de proiectare, regularitatea structurală, metodele de calcul."},
    "p1003": {"label": "P100-3/2019", "slug": "p100-3-2019",
              "title": "P100-3/2019 – Evaluarea seismică a clădirilor existente",
              "short": "P100-3/2019",
              "intro": "Codul de proiectare seismică P100-3/2019, partea a III-a – Prevederi pentru evaluarea seismică a clădirilor existente: metodologiile de evaluare, nivelurile de cunoaștere și factorii de încredere, indicatorii R1–R3 și clasele de risc seismic."},
    "cr113": {"label": "CR 1-1-3/2012", "slug": "cr-1-1-3-2012",
              "title": "CR 1-1-3/2012 – Evaluarea acțiunii zăpezii asupra construcțiilor",
              "short": "CR 1-1-3/2012 (zăpadă)",
              "intro": "Codul de proiectare CR 1-1-3/2012 – Evaluarea acțiunii zăpezii asupra construcțiilor: încărcarea pe sol, coeficienții de formă, de expunere și termic, aglomerările de zăpadă."},
    "cr114": {"label": "CR 1-1-4/2012", "slug": "cr-1-1-4-2012",
              "title": "CR 1-1-4/2012 – Evaluarea acțiunii vântului asupra construcțiilor",
              "short": "CR 1-1-4/2012 (vânt)",
              "intro": "Codul de proiectare CR 1-1-4/2012 – Evaluarea acțiunii vântului asupra construcțiilor: viteza și presiunea de referință, categoriile de teren, turbulența, răspunsul dinamic."},
}

# Pe site ajung doar grilele de test.
QUESTIONS = json.loads((ROOT / "questions_free.json").read_text())
COUNTS = {k: sum(1 for q in QUESTIONS if q["d"] == k) for k in DOMAINS}
FREE_TOTAL = len(QUESTIONS)
SIM_MINUTES = 60  # același ritm ca la examen: 120 de întrebări în 180 de minute

NB = " "


def esc(s):
    return html.escape(str(s), quote=True)


def fmt(s):
    """Aceeași tipografie ca în aplicație: spații nedespărțitoare și marcaje simple."""
    s = str(s)
    s = re.sub(r"\b(art|alin|lit|nr|pct|cap|Of)\. ", r"\1." + NB, s)
    s = re.sub(r"(\d) (s|m|ani|de ani|zile|luni|lei|de lei|kN|kPa|Pa|Hz|puncte|de puncte|persoane|de persoane)(?=$|[\s.,;:)/])", r"\1" + NB + r"\2", s)
    s = re.sub(r" (×|·|−|/) ", NB + r"\1 ", s)
    s = re.sub(r" (=|≤|<|>|≥|≈) (?=\d)", NB + r"\1" + NB, s)
    s = re.sub(r" (=|≤|<|>|≥|≈) ", NB + r"\1 ", s)
    s = re.sub(r"Rs (I{1,3}V?|IV)\b", "Rs" + NB + r"\1", s)
    s = html.escape(s, quote=False)
    s = re.sub(r"\*\*([^*]+)\*\*", r'<strong>\1</strong>', s)
    s = re.sub(r"\*([^*]+)\*", r"<i>\1</i>", s)
    s = re.sub(r"_\{([^}]+)\}", r"<sub>\1</sub>", s)
    s = re.sub(r"\^\{([^}]+)\}", r"<sup>\1</sup>", s)
    return s


def plain(s):
    """Text simplu pentru meta-descrieri și date structurate."""
    s = re.sub(r"\*\*?([^*]+)\*\*?", r"\1", str(s))
    s = re.sub(r"_\{([^}]+)\}", r"\1", s)
    s = re.sub(r"\^\{([^}]+)\}", r"\1", s)
    return s


ORDERED = re.compile(r"^\s*(\d|CC\d|clasa [IV]+\b|[<>≤≥]|Sub \d|Peste \d)")


def display_order(q):
    """Ordinea variantelor pe paginile statice. În aplicație variantele se amestecă la fiecare afișare;
    aici le amestecăm o singură dată, determinist, ca răspunsul corect să nu fie mereu pe aceeași literă.
    Variantele care formează un șir (valori numerice, clase) își păstrează ordinea firească."""
    import random
    if all(ORDERED.match(o) for o in q["o"]):
        return [0, 1, 2, 3]
    order = [0, 1, 2, 3]
    random.Random("grile-" + q["id"]).shuffle(order)
    return order


NAV = [
    ("/grile/expert-a1/", "Grile A1"),
    ("/ghid/examen-atestare-expert-tehnic/", "Ghid examen"),
    ("/ghid/legea-169-2026-experti-verificatori/", "Noul Cod"),
    ("/despre/", "Despre"),
]


def mailto(subject=""):
    if not CONFIG["contact_email"]:
        return ""
    q = ("?subject=" + subject.replace(" ", "%20")) if subject else ""
    return "mailto:" + CONFIG["contact_email"] + q


def layout(path, title, desc, body, *, schema=None, scripts="", og_type="website", current=None):
    canonical = BASE + path
    full_title = title if CONFIG["name"] in title else f"{title} – {CONFIG['name']}"
    nav = "".join(
        f'<a href="{href}"{" aria-current=\"page\"" if (current or path) == href else ""}>{esc(label)}</a>'
        for href, label in NAV)
    head_extra = ""
    if CONFIG["google_verification"]:
        head_extra += f'<meta name="google-site-verification" content="{esc(CONFIG["google_verification"])}">\n'
    if CONFIG["cf_beacon_token"]:
        head_extra += ("<script type=\"module\" src=\"https://static.cloudflareinsights.com/beacon.min.js\" "
                       f"data-cf-beacon='{{\"token\": \"{esc(CONFIG['cf_beacon_token'])}\"}}'></script>\n")
    ld = ""
    for s in (schema or []):
        ld += '<script type="application/ld+json">' + json.dumps(s, ensure_ascii=False) + "</script>\n"
    contact = mailto("Contact")
    foot_links = '<a href="/despre/">Despre</a><a href="/confidentialitate/">Confidențialitate</a>'
    if contact:
        foot_links += f'<a href="{contact}">Contact</a>'
    return f"""<!doctype html>
<html lang="ro">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{esc(full_title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{canonical}">
<meta property="og:site_name" content="{esc(CONFIG['name'])}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{canonical}">
<meta property="og:type" content="{og_type}">
<meta property="og:locale" content="ro_RO">
<meta property="og:image" content="{BASE}/assets/og.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#FAF9F6" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#151413" media="(prefers-color-scheme: dark)">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="preload" href="/assets/fonts/ibm-plex-sans-latin-400-normal.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="/assets/site.css?v={CONFIG['updated_iso']}">
{head_extra}{ld}</head>
<body>
<a class="skip" href="#continut">Sari la conținut</a>
<header class="site-head"><div class="wrap">
<a class="brand" href="/"><span class="brand-mark" aria-hidden="true">GA</span><span class="brand-name">{esc(CONFIG['name'])}</span><span class="beta">beta</span></a>
<nav class="site-nav" aria-label="Navigare principală">{nav}</nav>
</div></header>
<main id="continut" class="site-main wrap">
{body}
</main>
<footer class="site-foot"><div class="wrap">
<p>{esc(CONFIG['name'])} este un site independent, fără legătură cu MDLPA sau cu comisiile de examinare. Grilele sunt material de pregătire redactat pe baza textelor oficiale publicate și nu reproduc subiecte de examen. În caz de diferență, textul oficial în vigoare prevalează.</p>
<p>Legislație verificată la {CONFIG['law_checked']}. Ultima actualizare a site-ului: {CONFIG['updated_human']}.</p>
<nav aria-label="Informații">{foot_links}</nav>
</div></footer>
{scripts}</body>
</html>
"""


def write(path, content):
    target = OUT / path.lstrip("/")
    if path.endswith("/"):
        target = target / "index.html"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


def crumbs(items):
    """items: [(href, label), ...]; ultimul element e pagina curentă."""
    parts = [f'<a href="{h}">{esc(l)}</a>' for h, l in items[:-1]] + [esc(items[-1][1])]
    ld = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "name": l, "item": BASE + h} for i, (h, l) in enumerate(items)]}
    return '<p class="crumbs">' + " / ".join(parts) + "</p>", ld


NEXT_TEXT = ("Grile Atestare este acum în versiune de test, cu acces gratuit. Dacă grilele se dovedesc utile și "
             "interesul e suficient, vom trece la o versiune extinsă, cu mai multe tipuri de grile (alte domenii de "
             "atestare, verificatori de proiecte, responsabili tehnici cu execuția, diriginți de șantier), "
             "disponibilă pe bază de cont și abonament.")


def waitlist_box(heading="Ce urmează"):
    text = NEXT_TEXT + " Dacă te-ar interesa, lasă-ne un semn și te anunțăm."
    if CONFIG["waitlist_url"]:
        btn = f'<a class="btn primary" href="{esc(CONFIG["waitlist_url"])}" target="_blank" rel="noopener">Anunță-mă</a>'
        note = '<span class="small">Te anunțăm doar la lansare. Te poți dezabona oricând.</span>'
    elif CONFIG["contact_email"]:
        btn = f'<a class="btn primary" href="{mailto("Anunta-ma")}">Anunță-mă prin e-mail</a>'
        note = f'<span class="small">Sau scrie la {esc(CONFIG["contact_email"])} cu subiectul „Anunță-mă”.</span>'
    else:
        btn, note = "", '<span class="small">Formularul de înscriere apare în curând.</span>'
    return f'<section class="box" id="anunta-ma"><h2>{esc(heading)}</h2><p>{text}</p><div class="row">{btn}{note}</div></section>'


# ---------------------------------------------------------------- Pagini

def cartus_html(cells):
    return '<div class="cartus">' + "".join(
        f'<div class="cell"><span class="k">{k}</span><span class="v">{v}</span></div>' for k, v in cells) + "</div>"


def sample_html(q):
    """Întrebare rezolvabilă direct pe prima pagină: variantele sunt butoane, răspunsul apare după alegere."""
    order = display_order(q)
    letters = "abcd"
    opts = "".join(
        f'<li><button class="opt" data-o="{orig}"><span class="letter">{letters[pos]}</span>'
        f'<span class="txt">{fmt(q["o"][orig])}</span><span class="mark"></span></button></li>'
        for pos, orig in enumerate(order))
    right_letter = letters[order.index(q["c"])]
    return f"""<div class="sample" id="sample" data-c="{q['c']}" data-letter="{right_letter}">
<p class="sample-title">Încearcă o întrebare din grile</p>
{cartus_html([("Exemplu", f"1 din {FREE_TOTAL}"), ("Act normativ", fmt(DOMAINS[q['d']]['label']))])}
<p class="stem">{fmt(q['q'])}</p>
<ol class="opts">{opts}</ol>
<section class="note" hidden aria-live="polite">
<p class="res"></p>
<p>{fmt(q['e'])}</p>
{cartus_html([("Temei legal", fmt(q['r']))])}
<p><a href="/grile/expert-a1/">Continuă cu celelalte întrebări</a></p>
</section>
</div>
<script>
(function () {{
  var box = document.getElementById("sample"), c = box.getAttribute("data-c"), L = box.getAttribute("data-letter");
  box.addEventListener("click", function (ev) {{
    var b = ev.target.closest(".opt"); if (!b || b.disabled) return;
    var chosen = b.getAttribute("data-o");
    box.querySelectorAll(".opt").forEach(function (o) {{
      o.disabled = true;
      var v = o.getAttribute("data-o");
      if (v === c) {{ o.classList.add("is-right"); o.querySelector(".mark").textContent = "Corect"; }}
      else if (v === chosen) {{ o.classList.add("is-wrong"); o.querySelector(".mark").textContent = "Ales de tine"; }}
      else o.classList.add("is-dim");
    }});
    var note = box.querySelector(".note"), ok = chosen === c;
    note.classList.toggle("bad", !ok);
    note.querySelector(".res").textContent = ok ? "Corect." : "Greșit. Răspunsul corect este " + L + ".";
    note.hidden = false;
  }});
}})();
</script>"""


def page_home():
    total = FREE_TOTAL
    rows = "".join(
        f'<tr><td><a href="/grile/expert-a1/{d["slug"]}/">{fmt(d["short"])}</a></td><td>{COUNTS[k]}</td></tr>'
        for k, d in DOMAINS.items())
    sample = next(q for q in QUESTIONS if q["id"] == "catuc-13")
    body = f"""
<section class="hero">
  <div>
    <h1>Grile pentru atestarea ca expert tehnic A1, după noul Cod al construcțiilor</h1>
    <p class="lead">{total} de întrebări din Legea nr.{NB}169/2026, P100-1, P100-3 și codurile de zăpadă și vânt. Fiecare are explicație și articolul din care e luată.</p>
    <div class="actions">
      <a class="btn primary" href="/grile/expert-a1/">Începe antrenamentul</a>
      <a class="btn" href="/grile/expert-a1/#simulare">Fă o simulare de {SIM_MINUTES} de minute</a>
    </div>
    <p class="meta">Gratuit, fără cont. Versiune de test, actualizată după Legea nr.{NB}169/2026, aplicabilă din 25{NB}august{NB}2026.</p>
  </div>
  {sample_html(sample)}
</section>

<section class="sec">
  <h2>Ce s-a schimbat în august 2026</h2>
  <p>Din 25 august 2026 se aplică Codul amenajării teritoriului, urbanismului și construcțiilor (Legea nr.{NB}169/2026). Codul a abrogat integral Legea nr.{NB}50/1991 și Legea nr.{NB}350/2001 și cea mai mare parte a Legii nr.{NB}10/1995. Culegerile de grile scrise înainte de această dată nu mai acoperă legislația de bază. Aici, fiecare întrebare pe noul Cod are trimitere la articol.</p>
</section>

<section class="sec">
  <h2>Cum lucrezi</h2>
  <dl class="deflist">
    <dt>Antrenament</dt><dd>Lucrezi pe un act normativ sau pe toate. După fiecare răspuns vezi explicația și temeiul legal, iar greșelile se adună într-o listă separată.</dd>
    <dt>Simulare</dt><dd>{total} de întrebări în ordine aleatorie, în {SIM_MINUTES} de minute, același ritm ca la examen. Punctajul se raportează la 120, cu pragul de 75, iar la final primești fișa de corectare.</dd>
    <dt>Pagini de studiu</dt><dd>Pentru fiecare act normativ, întrebările cu răspunsuri, de citit înainte de examen.</dd>
    <dt>Fără cont</dt><dd>Progresul rămâne pe telefonul sau calculatorul tău. Dacă închizi pagina în timpul simulării, continui de unde ai rămas.</dd>
  </dl>
</section>

<section class="sec">
  <h2>Ce acoperă grilele</h2>
  <div class="tbl-wrap"><table class="tbl">
    <thead><tr><th>Act normativ</th><th>Întrebări</th></tr></thead>
    <tbody>{rows}</tbody>
    <tfoot><tr><td>Total</td><td>{total}</td></tr></tfoot>
  </table></div>
</section>

{waitlist_box()}

<section class="sec">
  <h2>Cum sunt scrise grilele</h2>
  <p>Fiecare întrebare pornește de la un articol dintr-un act normativ publicat și are un singur răspuns corect. Explicația spune de ce e corect, iar temeiul legal îți arată unde să cauți. Grilele nu reproduc subiecte oficiale de examen. Dacă găsești o greșeală, semnaleaz-o de sub explicație și o corectăm. <a href="/despre/">Despre site</a></p>
</section>
"""
    schema = [{"@context": "https://schema.org", "@type": "WebSite", "name": CONFIG["name"], "url": BASE + "/",
               "inLanguage": "ro"}]
    return layout("/", "Grile atestare expert tehnic A1 după noul Cod al construcțiilor",
                  f"{total} de grile gratuite pentru atestarea ca expert tehnic A1 (MDLPA), cu explicații și temei legal, actualizate după Legea nr. 169/2026. Antrenament și simulare de examen.",
                  body, schema=schema)


def page_quiz():
    dom_labels = {k: d["label"] for k, d in DOMAINS.items()}
    cfg = {"domains": dom_labels, "storeKey": "grile-a1-free-v1", "simKey": "grile-a1-free-sim-v1",
           "simMinutes": SIM_MINUTES,
           "email": CONFIG["contact_email"], "waitlist": CONFIG["waitlist_url"]}
    data = json.dumps(QUESTIONS, ensure_ascii=False).replace("</", "<\\/")
    study = ", ".join(f'<a href="/grile/expert-a1/{d["slug"]}/">{fmt(d["label"])}</a>' for d in DOMAINS.values())
    cr, cr_ld = crumbs([("/", "Acasă"), ("/grile/expert-a1/", "Grile Expert A1")])
    body = f"""
{cr}
<header class="app-head">
  <div>
    <h1>Grile expert tehnic A1</h1>
    <p>Rezistență mecanică și stabilitate, construcții din beton, beton armat, zidărie și lemn. {FREE_TOTAL} de întrebări, legislație verificată la {CONFIG['law_checked'].replace(' ', NB)}.</p>
  </div>
  <div class="modes" role="group" aria-label="Mod de lucru">
    <button id="mode-practice" aria-pressed="true">Antrenament</button>
    <button id="mode-sim" aria-pressed="false">Simulare, {SIM_MINUTES} min</button>
  </div>
</header>

<div id="filters" class="filters" role="group" aria-label="Filtru pe acte normative"></div>

<div id="app" class="layout"><noscript><p>Pentru grilele interactive este nevoie de JavaScript. Întrebările se pot citi și în paginile de studiu de mai jos.</p></noscript></div>

<footer class="notes">
  <h2>Note</h2>
  <ol>
    <li>Întrebările sunt material de pregătire redactat pe baza textelor publicate. Nu reproduc subiecte oficiale de examen. Verifică forma în vigoare a fiecărui act înainte de examen.</li>
    <li>Procedura de atestare fixează punctajul maxim (120 de puncte), pragul de promovare (75 de puncte) și durata de regulă a examenului (3 ore). Numărul de întrebări și punctajul pe întrebare se stabilesc pentru fiecare sesiune.</li>
    <li>Simularea gratuită are {FREE_TOTAL} de întrebări în {SIM_MINUTES} de minute, adică același ritm ca la examen (un minut și jumătate pe întrebare). Punctajul se raportează la 120, deci pragul de 75 de puncte înseamnă 25 de răspunsuri corecte din 40.</li>
    <li>Pagini de studiu, cu întrebările gratuite și răspunsurile lor: {study}.</li>
    <li>Surse: Legea nr.{NB}169/2026 privind Codul amenajării teritoriului, urbanismului și construcțiilor (M.{NB}Of. nr.{NB}661 din 10.08.2026, rectificată în M.{NB}Of. nr.{NB}862 din 14.10.2026); Procedura aprobată prin Ordinul MDLPA nr.{NB}817/2021; Regulamentul aprobat prin Ordinul MDLPA nr.{NB}895/2023; Regulamentul aprobat prin HG nr.{NB}925/1995, cu modificările aduse prin HG nr.{NB}742/2018; P100-1/2013; P100-3/2019; CR 1-1-3/2012; CR 1-1-4/2012.</li>
  </ol>
</footer>
<script type="application/json" id="cfg">{json.dumps(cfg, ensure_ascii=False)}</script>
<script type="application/json" id="data">{data}</script>
"""
    scripts = f'<script src="/assets/quiz.js?v={CONFIG["updated_iso"]}"></script>\n'
    return layout("/grile/expert-a1/", "Grile Expert A1 – antrenament și simulare de examen",
                  f"{FREE_TOTAL} de grile gratuite pentru atestarea ca expert tehnic A1: antrenament pe acte normative, cu explicații și temei legal, și simulare de examen cu punctaj raportat la 120.",
                  body, schema=[cr_ld], scripts=scripts)


def page_domain(key):
    d = DOMAINS[key]
    qs = [q for q in QUESTIONS if q["d"] == key]
    path = f"/grile/expert-a1/{d['slug']}/"
    items = "".join(f"""<li id="{q['id']}">
<span class="qn">Întrebarea {i + 1} din {len(qs)}</span>
<p class="stem">{fmt(q['q'])}</p>
<ol class="abcd">{''.join(f'<li><span class="l">{"abcd"[j]})</span><span>{fmt(q["o"][o])}</span></li>' for j, o in enumerate(display_order(q)))}</ol>
<details class="ans"><summary>Arată răspunsul</summary>
<div class="inner">
<p class="right">Răspuns corect: {"abcd"[display_order(q).index(q['c'])]}) {fmt(q['o'][q['c']])}</p>
<p>{fmt(q['e'])}</p>
{cartus_html([("Temei legal", fmt(q['r']))])}
<p><a href="/grile/expert-a1/?q={q['id']}">Rezolvă în aplicație</a></p>
</div>
</details>
</li>""" for i, q in enumerate(qs))
    others = ", ".join(f'<a href="/grile/expert-a1/{o["slug"]}/">{fmt(o["label"])}</a>'
                        for k, o in DOMAINS.items() if k != key)
    cr, cr_ld = crumbs([("/", "Acasă"), ("/grile/expert-a1/", "Grile Expert A1"), (path, d["label"])])
    body = f"""
<div class="prose">
{cr}
<h1>Grile {fmt(d['short'])} pentru examenul de expert tehnic A1</h1>
<p class="lede">{len(qs)} întrebări gratuite cu răspunsuri, explicații și temei legal.</p>
<p>{fmt(d['intro'])}</p>
<p>Încearcă întâi să răspunzi singur, apoi deschide răspunsul. Pentru notare și progres salvat, <a href="/grile/expert-a1/?f={key}">rezolvă aceleași întrebări interactiv</a>.</p>
</div>
<ol class="qlist">{items}</ol>
<section class="sec"><h2>Alte acte normative</h2><p>{others}</p></section>
{waitlist_box()}
"""
    desc = f"{len(qs)} grile {plain(d['short'])} pentru atestarea ca expert tehnic A1, cu răspunsuri, explicații și articolul din lege."
    return path, layout(path, f"Grile {plain(d['short'])} – expert tehnic A1, cu răspunsuri", desc, body,
                        schema=[cr_ld], current="/grile/expert-a1/")


def page_guide_exam():
    path = "/ghid/examen-atestare-expert-tehnic/"
    cr, cr_ld = crumbs([("/", "Acasă"), (path, "Ghidul examenului")])
    faqs = [
        ("Câte puncte trebuie pentru a promova examenul de atestare?",
         "Procedura de atestare stabilește un punctaj maxim de 120 de puncte și un prag de promovare de 75 de puncte."),
        ("Cât durează examenul?",
         "Durata de regulă a testului-grilă este de 3 ore, potrivit Procedurii aprobate prin Ordinul MDLPA nr. 817/2021."),
        ("Ce lege trebuie studiată după august 2026?",
         "Din 25 august 2026 se aplică Legea nr. 169/2026 privind Codul amenajării teritoriului, urbanismului și construcțiilor, care a abrogat integral Legea nr. 50/1991 și Legea nr. 350/2001 și cea mai mare parte a Legii nr. 10/1995. Regulamentul aprobat prin HG nr. 925/1995 rămâne în vigoare până la modificarea lui."),
        ("Pot avea materiale la examen?",
         "Regulamentul sesiunii din 2023 (Ordinul MDLPA nr. 895/2023) permitea candidaților referințele bibliografice pe care le considerau necesare. Regula se stabilește prin regulamentul fiecărei sesiuni, așa că trebuie verificată pentru sesiunea la care te înscrii."),
    ]
    faq_ld = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faqs]}
    art_ld = {"@context": "https://schema.org", "@type": "Article", "headline": "Examenul de atestare ca expert tehnic: cum arată și cum te pregătești",
              "inLanguage": "ro", "dateModified": CONFIG["updated_iso"], "mainEntityOfPage": BASE + path}
    faq_html = "".join(f"<h3>{esc(q)}</h3><p>{fmt(a)}</p>" for q, a in faqs)
    body = f"""
<article class="prose">
{cr}
<h1>Examenul de atestare ca expert tehnic: cum arată și cum te pregătești</h1>
<p class="lede">Ce prevede procedura MDLPA, ce s-a schimbat odată cu noul Cod al construcțiilor și cum îți împarți cele 3 ore.</p>
<p class="meta">Actualizat la {CONFIG['updated_human']}</p>

<div class="summary"><ul>
<li>Examenul este un test-grilă: maximum 120 de puncte, promovare de la 75 de puncte, durata de regulă 3 ore.</li>
<li>MDLPA organizează sesiunile de atestare; procedura prevede două sesiuni pe an, cu date stabilite.</li>
<li>Atestarea se dă pe domenii. A1 înseamnă rezistență mecanică și stabilitate pentru construcții din beton, beton armat, zidărie și lemn; A2, aceleași categorii de construcții, cu structură din metal.</li>
<li>Din 25 august 2026, legislația de bază este Legea nr.{NB}169/2026 (noul Cod), nu Legea nr.{NB}50/1991 și cea mai mare parte a Legii nr.{NB}10/1995.</li>
</ul></div>

<h2>Cine organizează examenul</h2>
<p>Atestarea tehnico-profesională a verificatorilor de proiecte și a experților tehnici se face după Procedura aprobată prin Ordinul MDLPA nr.{NB}817/2021, cu modificările ulterioare. Calendarul sesiunilor, condițiile de înscriere și bibliografia pe domenii se publică pe <a href="https://www.mdlpa.ro/pages/atestaritehnicoprofesionale" rel="noopener">pagina de atestări a MDLPA</a>. Verifică acolo datele sesiunii la care vrei să te înscrii.</p>

<h2>Cine se poate înscrie</h2>
<p>Procedura cere experiență profesională în domeniu. Pentru expertul tehnic, pragul este de 12 ani, din care cel puțin 4 în activități de proiectare. Pentru verificatorul de proiecte, de 8 ani, din care cel puțin 3 în proiectare. Noul Cod lasă stabilirea experienței necesare pe seama ordinului ministrului (art.{NB}436 alin.{NB}(1)), așa că verifică cerințele în forma în vigoare a procedurii.</p>

<h2>Cum se desfășoară și cum se notează</h2>
<ul>
<li>Baremul și varianta martor, adică formularul cu răspunsurile corecte marcate, le stabilește comisia centrală de examinare. Comisiile regionale corectează lucrările pe baza lor.</li>
<li>Punctajul maxim este de 120 de puncte, iar pragul de promovare de 75. Numărul de întrebări și punctele pe întrebare se stabilesc pentru fiecare sesiune.</li>
<li>Dacă la contestații un subiect se anulează pentru vicii de formulare, punctele lui se scad atât din punctajul maxim, cât și din pragul de promovare.</li>
</ul>
<p class="src">Procedura aprobată prin Ordinul MDLPA nr.{NB}817/2021, art.{NB}20, 22, 26 și 29–30.</p>

<h2>Ce s-a schimbat în bibliografie din august 2026</h2>
<p>Legea nr.{NB}169/2026 privind Codul amenajării teritoriului, urbanismului și construcțiilor se aplică din 25 august 2026. Codul a abrogat integral Legea nr.{NB}50/1991 și Legea nr.{NB}350/2001, iar din Legea nr.{NB}10/1995 a abrogat art.{NB}1–9, 11–40 și 42–44. Regulamentul de verificare și expertizare tehnică aprobat prin HG nr.{NB}925/1995 rămâne în vigoare până la modificarea lui.</p>
<p>Pentru experți și verificatori, Codul aduce clasele de consecințe CC1–CC4, nivelurile de verificare NVP1–NVP4 și reguli noi de răspundere și sancțiuni. Le-am adunat, cu articolele, în <a href="/ghid/legea-169-2026-experti-verificatori/">ghidul despre noul Cod</a>.</p>
<p class="src">Legea nr.{NB}169/2026, art.{NB}575–577.</p>

<h2>Cum îți împarți cele 3 ore</h2>
<ul>
<li>Dacă sesiunea are 120 de întrebări, în 180 de minute ai în medie un minut și jumătate pe întrebare. Răspunde întâi la ce știi sigur, marchează restul și revino la ele.</li>
<li>Dacă regulamentul sesiunii permite bibliografia, exersează cu ea deschisă. Contează cât de repede găsești articolul, nu doar ce ai memorat.</li>
<li>Începe cu noul Cod: e materia cu cele mai multe schimbări, iar materialele de pregătire scrise înainte de august 2026 nu îl acoperă.</li>
<li>Lucrează cu cronometru: simularea gratuită are 40 de întrebări în 60 de minute, același ritm ca la examen. Reia apoi doar întrebările greșite.</li>
</ul>
<p><a class="btn primary" href="/grile/expert-a1/#simulare">Fă o simulare gratuită</a></p>

<h2>După atestare</h2>
<p>Potrivit noului Cod, dreptul de practică al expertului tehnic se acordă pe durată nedeterminată și se confirmă din 5 în 5 ani, pe baza experienței și a cursurilor de pregătire profesională continuă. Specialiștii atestați încheie asigurare de răspundere civilă profesională pe perioade de cel puțin un an, pe toată durata exercitării profesiei.</p>
<p class="src">Legea nr.{NB}169/2026, art.{NB}436 alin.{NB}(3), (4) și (7); art.{NB}556.</p>

<h2>Întrebări frecvente</h2>
{faq_html}
</article>
{waitlist_box()}
"""
    return path, layout(path, "Examenul de atestare ca expert tehnic: cum arată și cum te pregătești",
                        "Cum arată examenul MDLPA de atestare ca expert tehnic sau verificator: test-grilă de 120 de puncte, prag de 75, 3 ore. Ce s-a schimbat în bibliografie după Legea nr. 169/2026.",
                        body, schema=[cr_ld, art_ld, faq_ld], og_type="article")


def page_guide_code():
    path = "/ghid/legea-169-2026-experti-verificatori/"
    cr, cr_ld = crumbs([("/", "Acasă"), (path, "Noul Cod pentru experți și verificatori")])
    art_ld = {"@context": "https://schema.org", "@type": "Article",
              "headline": "Legea nr. 169/2026 pentru experți tehnici și verificatori de proiecte",
              "inLanguage": "ro", "dateModified": CONFIG["updated_iso"], "mainEntityOfPage": BASE + path}
    body = f"""
<article class="prose">
{cr}
<h1>Legea nr.{NB}169/2026 pentru experți tehnici și verificatori de proiecte</h1>
<p class="lede">Ce trebuie să știi din noul Cod al construcțiilor pentru examenul de atestare și pentru practică, cu articolul la fiecare regulă.</p>
<p class="meta">Actualizat la {CONFIG['updated_human']}. Text verificat după forma publicată în M.{NB}Of. nr.{NB}661/2026, rectificată în M.{NB}Of. nr.{NB}862/2026.</p>

<nav class="toc"><ol>
<li><a href="#aplicare">Aplicare și abrogări</a></li>
<li><a href="#clase">Clasele de consecințe</a></li>
<li><a href="#verificare">Verificarea tehnică a proiectelor</a></li>
<li><a href="#expertiza">Expertiza tehnică</a></li>
<li><a href="#raspundere">Răspundere, asigurare, sancțiuni</a></li>
<li><a href="#durata">Durata de existență și urmărirea în timp</a></li>
</ol></nav>

<h2 id="aplicare">1. Aplicare și abrogări</h2>
<ul>
<li>Legea a fost publicată în Monitorul Oficial nr.{NB}661 din 10 august 2026 și se aplică din 25 august 2026, la 15 zile de la publicare. Aplicarea nu depinde de apariția normelor metodologice. <span class="src">Art.{NB}575</span></li>
<li>Se abrogă integral Legea nr.{NB}50/1991, Legea nr.{NB}350/2001 și Ordinul nr.{NB}839/2009. Din Legea nr.{NB}10/1995 se abrogă art.{NB}1–9, 11–40 și 42–44. <span class="src">Art.{NB}576 alin.{NB}(3)</span></li>
<li>Rămân în vigoare, până la modificare, regulamentele aprobate prin HG nr.{NB}925/1995 (verificare și expertizare), HG nr.{NB}766/1997, HG nr.{NB}273/1994 (recepția) și HG nr.{NB}492/2018 (controlul de stat al calității). <span class="src">Art.{NB}577</span></li>
</ul>

<h2 id="clase">2. Clasele de consecințe</h2>
<ul>
<li>Construcțiile se încadrează în clasele de consecințe CC1–CC4. Echivalența cu sistemul vechi: CC4 ↔ categoria A ↔ clasa I; CC3 ↔ B ↔ II; CC2 ↔ C ↔ III; CC1 ↔ D ↔ IV. <span class="src">Art.{NB}370 alin.{NB}(5)</span></li>
<li>Se evaluează cinci feluri de consecințe (vieți omenești, economice, culturale, sociale, de mediu), iar încadrarea se face după cea mai severă dintre ele. <span class="src">Art.{NB}370 alin.{NB}(3) și (6)</span></li>
<li>Pragurile pentru pierderi de vieți: CC1 sub 5, CC2 sub 50, CC3 sub 500, CC4 peste 500. <span class="src">Art.{NB}370 alin.{NB}(7)–(11)</span></li>
<li>Încadrarea o face proiectantul. Încadrarea sub clasa indicată de Cod este interzisă; până la metodologia de încadrare, clasa se ia din anexa nr.{NB}6. Construcțiile care nu apar în anexă se asimilează motivat cu cea mai apropiată. <span class="src">Art.{NB}370 alin.{NB}(14)–(17)</span></li>
<li>Exemple din anexa nr.{NB}6: școlile și liceele cu peste 200 de persoane sunt în CC3; creșele și grădinițele în CC3, indiferent de capacitate; clădirile civile mai înalte de 45{NB}m cu peste 500 de persoane în CC4; centralele eoliene și fotovoltaice în CC1. <span class="src">Anexa nr.{NB}6</span></li>
</ul>
<p><a href="/grile/expert-a1/legea-169-2026/">Exersează: grile pe Legea nr.{NB}169/2026</a></p>

<h2 id="verificare">3. Verificarea tehnică a proiectelor</h2>
<ul>
<li>Proiectele construcțiilor din CC1 nu se verifică; răspunderea revine celor care le-au elaborat. Pentru CC2–CC4, verificarea o fac verificatori atestați care nu au participat la elaborarea proiectului. <span class="src">Art.{NB}440 alin.{NB}(1)–(3)</span></li>
<li>Nivelul de verificare urmează clasa de consecințe: CC1 → NVP1, CC2 → NVP2, CC3 → NVP3, CC4 → NVP4. <span class="src">Art.{NB}440 alin.{NB}(4)</span></li>
<li>La NVP4 verificatorul face un calcul paralel și independent; diferențele față de calculul proiectantului nu pot depăși 5%, iar notele de calcul însoțesc referatul. <span class="src">Art.{NB}444 alin.{NB}(3)–(4); art.{NB}445 alin.{NB}(8)</span></li>
<li>Se verifică fazele PAC, PTh și DE, nu studiul de fezabilitate și nici proiectul real executat. <span class="src">Art.{NB}445 alin.{NB}(3)–(4)</span></li>
<li>Verificatorul aplică reglementările în vigoare la data depunerii documentației pentru autorizația de construire și nu are voie să intervină în alegerea sau modificarea soluțiilor de proiectare. <span class="src">Art.{NB}445 alin.{NB}(1) lit.{NB}a), alin.{NB}(9)–(10)</span></li>
<li>Verificatorul nu răspunde de dispozițiile de șantier, cu excepția consolidărilor și a monumentelor istorice. Pentru monumente este necesară atestare suplimentară. <span class="src">Art.{NB}445 alin.{NB}(5)–(7); art.{NB}440 alin.{NB}(5)</span></li>
</ul>

<h2 id="expertiza">4. Expertiza tehnică</h2>
<ul>
<li>Expertiza este obligatorie pentru fundamentarea intervențiilor, după dezastre sau accidente, la expirarea duratei de existență proiectate și pentru evaluarea influenței asupra vecinătăților. <span class="src">Art.{NB}437 alin.{NB}(2)</span></li>
<li>Expertul sau firma la care lucrează nu poate expertiza un proiect pe care l-a elaborat ori l-a verificat. <span class="src">Art.{NB}435 alin.{NB}(2)</span></li>
<li>Regula generală: se aplică reglementările de la data semnării contractului de expertiză. Când expertiza fundamentează un proiect, se aplică legislația de la data cererii de autorizare. <span class="src">Art.{NB}439 alin.{NB}(1) lit.{NB}b)</span></li>
<li>Dreptul de practică se acordă pe durată nedeterminată și se confirmă din 5 în 5 ani; după 70 de ani, condițiile de sănătate se confirmă anual. <span class="src">Art.{NB}436 alin.{NB}(3), (4) și (7)</span></li>
</ul>

<h2 id="raspundere">5. Răspundere, asigurare, sancțiuni</h2>
<ul>
<li>Verificatorul răspunde 10 ani de la predarea sau recepția construcției, iar pentru viciile structurii rezultate din nerespectarea normelor de proiectare, pe toată durata de existență. Răspunderea e limitată la NVP2 și avansată la NVP3 și NVP4, numai pentru elementele verificate. <span class="src">Art.{NB}446</span></li>
<li>Expertul răspunde pe toată durata de existență proiectată a construcției sau până la o nouă expertiză. <span class="src">Art.{NB}439 alin.{NB}(2) și (9)</span></li>
<li>Asigurarea de răspundere civilă profesională se încheie pe perioade de cel puțin un an, pe toată durata exercitării profesiei. <span class="src">Art.{NB}556</span></li>
<li>Expertiza incompletă sau care nu respectă reglementările se sancționează cu amendă de la 50.000 la 100.000 de lei; neprecizarea clasei de consecințe în proiect, cu amendă de la 10.000 la 20.000 de lei. <span class="src">Art.{NB}570</span></li>
<li>Expertizarea fără respectarea reglementărilor de stabilitate și rezistență, care pune în pericol viața persoanelor, este infracțiune: închisoare de la un an la 5 ani. <span class="src">Art.{NB}569</span></li>
</ul>

<h2 id="durata">6. Durata de existență și urmărirea în timp</h2>
<ul>
<li>Durata de existență normată: 100 de ani pentru monumente istorice, 50 de ani pentru construcțiile permanente, 25 de ani pentru construcțiile agricole, industriale și de depozitare. <span class="src">Art.{NB}368</span></li>
<li>Urmărirea comportării în timp se aplică tuturor construcțiilor, cu excepția celor din CC1. Un expert face investigarea amănunțită la 10 ani de la recepție și apoi din 10 în 10 ani. <span class="src">Art.{NB}550</span></li>
<li>Se instrumentează pentru monitorizare seismică construcțiile din CC4 și cele din CC3 din zone cu <i>a</i><sub>g</sub>{NB}≥{NB}0,35<i>g</i>. <span class="src">Art.{NB}550 alin.{NB}(14)</span></li>
<li>Perioada minimă de garanție a lucrărilor, dacă prin contract nu s-a prevăzut alta: 5 ani pentru CC3 și CC4, 3 ani pentru CC2, un an pentru CC1. <span class="src">Art.{NB}531</span></li>
</ul>
<p class="warn">Rezumatul nu înlocuiește textul legii. Înainte de examen sau de o decizie profesională, citește articolul în forma oficială în vigoare.</p>
<p><a class="btn primary" href="/grile/expert-a1/?f=catuc">Rezolvă grilele gratuite pe noul Cod</a></p>
</article>
{waitlist_box()}
"""
    return path, layout(path, "Legea nr. 169/2026 pentru experți tehnici și verificatori de proiecte",
                        "Ce schimbă noul Cod al construcțiilor (Legea nr. 169/2026) pentru experți tehnici și verificatori: clase de consecințe, niveluri de verificare NVP1–NVP4, răspundere, sancțiuni. Cu articolele de lege.",
                        body, schema=[cr_ld, art_ld], og_type="article")


def page_about():
    path = "/despre/"
    contact = CONFIG["contact_email"]
    contact_html = (f'Scrie-ne la <a href="{mailto("Contact")}">{esc(contact)}</a>.' if contact
                    else "Adresa de contact apare aici în curând.")
    body = f"""
<article class="prose">
<h1>Despre {esc(CONFIG['name'])}</h1>
<p class="lede">Grile de pregătire pentru examenele de atestare din construcții, scrise pe baza legislației în vigoare.</p>
<h2>Ce este</h2>
<p>{esc(CONFIG['name'])} oferă grile pentru examenul de atestare tehnico-profesională organizat de MDLPA. Prima colecție, pentru expertul tehnic A1, are {FREE_TOTAL} de întrebări de test, gratuite, cu antrenament explicat și simulare de examen. Site-ul este în versiune beta și nu cere cont.</p>
<h2>Cum sunt scrise întrebările</h2>
<ul>
<li>Fiecare întrebare pornește de la un articol, un punct sau o relație dintr-un act normativ publicat și are un singur răspuns corect.</li>
<li>Explicația spune de ce răspunsul e corect și, de multe ori, de ce celelalte variante sunt greșite.</li>
<li>Temeiul legal îți arată unde să cauți în text. Legea nr.{NB}169/2026 este citată după forma din Monitorul Oficial nr.{NB}661/2026, cu rectificarea din Monitorul Oficial nr.{NB}862/2026.</li>
<li>Grilele nu reproduc subiecte oficiale de examen și nu provin de la comisiile de examinare.</li>
</ul>
<h2>Independență</h2>
<p>Site-ul nu are legătură cu MDLPA, cu Inspectoratul de Stat în Construcții sau cu comisiile de examinare. Informațiile oficiale despre sesiuni și înscriere se găsesc pe <a href="https://www.mdlpa.ro/pages/atestaritehnicoprofesionale" rel="noopener">pagina de atestări a MDLPA</a>.</p>
<h2>Greșeli și sugestii</h2>
<p>Am verificat fiecare întrebare cu textul actului normativ, dar o greșeală poate scăpa. Dacă găsești una, folosește legătura „Semnalează o greșeală” de sub explicație sau scrie-ne. Corectăm și actualizăm data din subsolul site-ului. {contact_html}</p>
<h2>Ce urmează</h2>
<p>{NEXT_TEXT}</p>
</article>
{waitlist_box()}
"""
    return path, layout(path, "Despre site", f"Ce este {CONFIG['name']}, cum sunt scrise grilele pentru atestarea MDLPA și cum semnalezi o greșeală.", body)


def page_privacy():
    path = "/confidentialitate/"
    contact = CONFIG["contact_email"]
    contact_link = f'<a href="mailto:{esc(contact)}">{esc(contact)}</a>' if contact else "adresa din pagina Despre"
    if CONFIG["operator"]:
        op_line = f"Operatorul site-ului {esc(CONFIG['domain'])} este {esc(CONFIG['operator'])}, care poate fi contactat la {contact_link}."
    else:
        op_line = f"Site-ul {esc(CONFIG['domain'])} poate fi contactat la {contact_link}."
    waitlist_sec = ("""<h2>Lista de așteptare</h2>
<p>Dacă te înscrii pe lista de așteptare, colectăm adresa de e-mail și, opțional, domeniul de atestare care te interesează, prin Google Forms. Le folosim doar ca să te anunțăm când apar grile noi. Temeiul este consimțământul tău, pe care îl poți retrage oricând, printr-un e-mail la adresa de mai sus. Păstrăm datele până la retragerea consimțământului sau până la închiderea listei și nu le transmitem altor persoane.</p>
""" if CONFIG["waitlist_url"] else "")
    body = f"""
<article class="prose">
<h1>Politica de confidențialitate</h1>
<p class="meta">Ultima actualizare: {CONFIG['updated_human']}</p>
<p>{op_line}</p>
<h2>Ce date nu colectăm</h2>
<p>Site-ul nu are conturi de utilizator și nu folosește cookie-uri de urmărire sau de publicitate.</p>
<h2>Progresul la grile</h2>
<p>Răspunsurile, progresul la antrenament și simularea în curs se salvează doar în browserul tău (localStorage), pe dispozitivul pe care lucrezi. Nu ajung la noi. Le poți șterge din pagina de grile („Șterge progresul”) sau din setările browserului.</p>
<h2>Statistici de trafic</h2>
<p>Folosim Cloudflare Web Analytics, un serviciu care numără vizitele fără cookie-uri și fără să identifice vizitatorii. Datele sunt agregate: pagini vizitate, țara, tipul de dispozitiv și sursa vizitei.</p>
{waitlist_sec}<h2>E-mailurile trimise de tine</h2>
<p>Dacă ne scrii, de exemplu ca să semnalezi o greșeală sau ca să fii anunțat când apar grile noi, folosim adresa și mesajul doar în acest scop: ca să-ți răspundem, să corectăm grila sau să te anunțăm. Poți cere oricând ștergerea lor.</p>
<h2>Drepturile tale</h2>
<p>Ai dreptul de acces, de rectificare, de ștergere, de restricționare a prelucrării, de opoziție și la portabilitatea datelor, precum și dreptul de a depune plângere la Autoritatea Națională de Supraveghere a Prelucrării Datelor cu Caracter Personal (www.dataprotection.ro).</p>
</article>
"""
    return path, layout(path, "Politica de confidențialitate", f"Ce date prelucrează {CONFIG['name']}: fără conturi și fără cookie-uri de urmărire; progresul rămâne în browserul tău.", body)


def page_404():
    body = """
<div class="prose">
<h1>Pagina nu există</h1>
<p>Adresa nu corespunde niciunei pagini. Poate cauți <a href="/grile/expert-a1/">grilele pentru expert A1</a> sau <a href="/ghid/examen-atestare-expert-tehnic/">ghidul examenului</a>.</p>
</div>
"""
    return layout("/404.html", "Pagina nu există", "Pagina căutată nu există.", body)


def favicon():
    return """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
<rect width="64" height="64" rx="8" fill="#2E3A9A"/>
<text x="32" y="42" text-anchor="middle" font-family="'Arial Narrow', 'Roboto Condensed', Arial, sans-serif" font-size="28" font-weight="700" fill="#FFFFFF">GA</text>
</svg>
"""


def og_image(dest):
    from io import BytesIO
    from fontTools.ttLib import TTFont
    from PIL import Image, ImageDraw, ImageFont

    cache = {}

    def font(name, size):
        key = (name, size)
        if key not in cache:
            tt = TTFont(ROOT / "assets/fonts" / name)
            tt.flavor = None
            buf = BytesIO(); tt.save(buf); buf.seek(0)
            cache[key] = ImageFont.truetype(buf, size)
        return cache[key]

    W, H = 1200, 630
    paper, ink, pencil, line, stamp = (255, 255, 255), (31, 35, 40), (91, 99, 107), (208, 213, 217), (46, 58, 154)
    img = Image.new("RGB", (W, H), paper)
    d = ImageDraw.Draw(img)

    def draw(x, y, text, size, weight, fill, family="ibm-plex-sans"):
        lat = font(f"{family}-latin-{weight}-normal.woff2", size)
        ext = font(f"{family}-latin-ext-{weight}-normal.woff2", size)
        for ch in text:
            f = ext if ord(ch) > 0xFF else lat
            d.text((x, y), ch, font=f, fill=fill)
            x += f.getlength(ch)
        return x

    # marca
    d.rounded_rectangle([80, 80, 136, 136], radius=6, fill=stamp)
    draw(88, 88, "GA", 34, 600, (255, 255, 255), family="ibm-plex-sans-condensed")
    draw(156, 92, "Grile Atestare", 34, 600, ink)
    draw(80, 200, "Grile pentru atestarea ca expert tehnic A1,", 52, 600, ink)
    draw(80, 268, "după noul Cod al construcțiilor", 52, 600, ink)
    draw(80, 360, f"{FREE_TOTAL} de întrebări cu explicație și temei legal.", 32, 400, pencil)
    draw(80, 404, "Antrenament și simulare de examen, fără cont.", 32, 400, pencil)
    # cartuș
    x0, y0, x1, y1 = 80, 480, W - 80, 560
    d.rectangle([x0, y0, x1, y1], outline=ink, width=2)
    cols = [x0, 460, 820, x1]
    for x in cols[1:-1]:
        d.line([(x, y0), (x, y1)], fill=line, width=1)
    cells = [("Site", "grileatestare.ro"), ("Act normativ", "Legea nr. 169/2026"), ("Acces", "gratuit")]
    for (k, v), xa in zip(cells, cols[:-1]):
        draw(xa + 16, y0 + 10, k, 20, 500, pencil, family="ibm-plex-sans-condensed")
        draw(xa + 16, y0 + 36, v, 28, 600, ink, family="ibm-plex-sans-condensed")
    img.save(dest, "PNG", optimize=True)


def main():
    if OUT.exists():
        for p in OUT.iterdir():
            if p.name == ".git":
                continue
            shutil.rmtree(p) if p.is_dir() else p.unlink()
    OUT.mkdir(exist_ok=True)
    shutil.copytree(ROOT / "assets", OUT / "assets", dirs_exist_ok=True)

    pages = {"/": page_home(), "/grile/expert-a1/": page_quiz()}
    for key in DOMAINS:
        p, c = page_domain(key)
        pages[p] = c
    for fn in (page_guide_exam, page_guide_code, page_about, page_privacy):
        p, c = fn()
        pages[p] = c
    for p, c in pages.items():
        write(p, c)
    (OUT / "404.html").write_text(page_404(), encoding="utf-8")
    (OUT / "favicon.svg").write_text(favicon(), encoding="utf-8")
    og_image(OUT / "assets/og.png")
    (OUT / "CNAME").write_text(CONFIG["domain"] + "\n")
    (OUT / ".nojekyll").write_text("")
    (OUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {BASE}/sitemap.xml\n")
    urls = "".join(f"<url><loc>{BASE}{p}</loc><lastmod>{CONFIG['updated_iso']}</lastmod></url>\n" for p in pages)
    (OUT / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + urls + "</urlset>\n")
    print(f"{len(pages)} pagini generate în {OUT}")


if __name__ == "__main__":
    main()
