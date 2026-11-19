/* Grile Atestare — antrenament și simulare de examen.
   Datele întrebărilor vin din <script id="data">, configurarea din <script id="cfg">. */
(function () {
  "use strict";
  var CFG = JSON.parse(document.getElementById("cfg").textContent);
  var DOMAINS = CFG.domains;
  var LETTERS = ["a", "b", "c", "d"];
  var SIM_MINUTES = CFG.simMinutes || 180;
  var MAX_POINTS = 120;
  var PASS_POINTS = 75;
  var STORE_KEY = CFG.storeKey;
  var SIM_KEY = CFG.simKey;
  var NB = " ";
  var ALL = JSON.parse(document.getElementById("data").textContent);
  var byId = {};
  ALL.forEach(function (q) { byId[q.id] = q; });

  function load(key) { try { return JSON.parse(localStorage.getItem(key)) || null; } catch (e) { return null; } }
  function save() { try { localStorage.setItem(STORE_KEY, JSON.stringify({ practice: state.practice, best: state.best })); } catch (e) {} }
  function saveSim() { try { if (state.sim) localStorage.setItem(SIM_KEY, JSON.stringify(state.sim)); else localStorage.removeItem(SIM_KEY); } catch (e) {} }

  function shuffle(arr) {
    var a = arr.slice();
    for (var i = a.length - 1; i > 0; i--) { var j = Math.floor(Math.random() * (i + 1)); var t = a[i]; a[i] = a[j]; a[j] = t; }
    return a;
  }
  function perms(ids) { var m = {}; ids.forEach(function (id) { m[id] = shuffle([0, 1, 2, 3]); }); return m; }
  /* Acord numeral–substantiv: 1 întrebare, 2–19 întrebări, 20+ de întrebări. */
  function num(n, sg, pl) {
    if (n === 1) return "1 " + sg;
    var r = n % 100;
    return n + (n !== 0 && (r === 0 || r >= 20) ? " de " : " ") + pl;
  }
  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }

  /* Tipografie: spații nedespărțitoare după abrevieri și între număr și unitate,
     apoi marcaje *italic*, **accent**, _{indice}, ^{exponent}. */
  function fmt(s) {
    s = String(s)
      .replace(/\b(art|alin|lit|nr|pct|cap|Of)\. /g, "$1." + NB)
      .replace(/(\d) (s|m|ani|de ani|zile|luni|lei|de lei|kN|kPa|Pa|Hz|puncte|de puncte|persoane|de persoane)(?=$|[\s.,;:)\/])/g, "$1" + NB + "$2")
      .replace(/ (×|·|−|\/) /g, NB + "$1 ")
      .replace(/ (=|≤|<|>|≥|≈) (?=\d)/g, NB + "$1" + NB)
      .replace(/ (=|≤|<|>|≥|≈) /g, NB + "$1 ")
      .replace(/Rs (I{1,3}V?|IV)\b/g, "Rs" + NB + "$1");
    s = esc(s)
      .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
      .replace(/\*([^*]+)\*/g, "<i>$1</i>")
      .replace(/_\{([^}]+)\}/g, "<sub>$1</sub>")
      .replace(/\^\{([^}]+)\}/g, "<sup>$1</sup>");
    return s;
  }

  function cartus(cells) {
    return '<div class="cartus">' + cells.map(function (c) {
      return '<div class="cell' + (c[4] ? " " + c[4] : "") + '"><span class="k">' + c[0] + '</span><span class="v' + (c[2] ? " " + c[2] : "") + '"' + (c[3] ? ' id="' + c[3] + '"' : "") + ">" + c[1] + "</span></div>";
    }).join("") + "</div>";
  }

  function reportLink(q) {
    if (!CFG.email) return "";
    var subj = "Greșeală în grila " + q.id;
    var body = "Întrebarea: " + q.q + "\n\nCe crezi că e greșit:\n";
    return '<a class="report" href="mailto:' + CFG.email + "?subject=" + encodeURIComponent(subj) + "&body=" + encodeURIComponent(body) + '">Semnalează o greșeală la această întrebare</a>';
  }

  function waitlistHTML() {
    if (!CFG.waitlist) return "";
    return '<section class="blk"><h2>Ce urmează</h2><p class="hint">Dacă interesul e suficient, vom trece la o versiune extinsă, cu mai multe tipuri de grile, pe bază de cont și abonament.</p>' +
      '<a class="btn" href="' + esc(CFG.waitlist) + '" target="_blank" rel="noopener">Anunță-mă</a></section>';
  }

  var saved = load(STORE_KEY) || {};
  var state = {
    mode: "practice",
    filter: "all",
    practice: saved.practice || {},
    best: saved.best || null,
    pIdx: 0,
    pPerm: perms(ALL.map(function (q) { return q.id; })),
    confirmReset: false,
    reviewAll: false,
    sim: null
  };

  /* Reluare simulare întreruptă (de exemplu, pagina închisă în timpul simulării). */
  var pending = load(SIM_KEY);
  if (pending && pending.order && pending.order.every(function (id) { return byId[id]; })) {
    state.sim = pending;
    state.sim.confirm = false;
    if (!pending.done) state.mode = "sim";
  }

  /* Legături directe: ?q=ID deschide întrebarea, ?f=act filtrează, #simulare deschide simularea. */
  (function deepLink() {
    var m = /[?&]q=([\w-]+)/.exec(location.search);
    var f = /[?&]f=(\w+)/.exec(location.search);
    var running = state.sim && !state.sim.done;
    if (m && byId[m[1]] && !running) {
      state.mode = "practice"; state.filter = "all";
      state.pIdx = ALL.indexOf(byId[m[1]]);
    } else if (f && DOMAINS[f[1]] && !running) {
      state.mode = "practice"; state.filter = f[1]; state.pIdx = 0;
    } else if (location.hash === "#simulare") {
      state.mode = "sim";
    }
  })();

  var app = document.getElementById("app");
  var filters = document.getElementById("filters");

  function practiceList() {
    return ALL.filter(function (q) {
      if (state.filter === "all") return true;
      if (state.filter === "wrong") return state.practice[q.id] !== undefined && state.practice[q.id] !== q.c;
      return q.d === state.filter;
    });
  }

  function renderFilters() {
    if (state.mode !== "practice") { filters.hidden = true; return; }
    filters.hidden = false;
    var counts = {};
    ALL.forEach(function (q) { counts[q.d] = (counts[q.d] || 0) + 1; });
    var wrong = ALL.filter(function (q) { return state.practice[q.id] !== undefined && state.practice[q.id] !== q.c; }).length;
    var items = [["all", "Toate", ALL.length]];
    Object.keys(DOMAINS).forEach(function (k) { items.push([k, DOMAINS[k], counts[k] || 0]); });
    items.push(["wrong", "Greșite", wrong]);
    filters.innerHTML = items.map(function (it) {
      return '<button id="f-' + it[0] + '" data-f="' + it[0] + '" aria-pressed="' + (state.filter === it[0]) + '">' + fmt(it[1]) + ' <span class="n">(' + it[2] + ")</span></button>";
    }).join("");
  }

  function optionsHTML(q, perm, chosen, reveal) {
    return '<ol class="opts">' + perm.map(function (orig, pos) {
      var cls = "opt", mark = "";
      if (reveal) {
        if (orig === q.c) { cls += " is-right"; mark = "Corect"; }
        else if (orig === chosen) { cls += " is-wrong"; mark = "Ales de tine"; }
        else cls += " is-dim";
      }
      var pressed = !reveal && orig === chosen;
      return '<li><button class="' + cls + '" data-o="' + orig + '" aria-pressed="' + pressed + '"' + (reveal ? " disabled" : "") + ">" +
        '<span class="letter">' + LETTERS[pos] + '</span><span class="txt">' + fmt(q.o[orig]) + '</span><span class="mark">' + mark + "</span></button></li>";
    }).join("") + "</ol>";
  }

  function letterOf(perm, orig) { return LETTERS[perm.indexOf(orig)]; }

  function noteHTML(q, perm, chosen) {
    var ok = chosen === q.c;
    return '<section class="note' + (ok ? "" : " bad") + '" aria-live="polite">' +
      '<p class="res">' + (ok ? "Corect." : "Greșit. Răspunsul corect este " + letterOf(perm, q.c) + ".") + "</p>" +
      "<p>" + fmt(q.e) + "</p>" +
      cartus([["Temei legal", fmt(q.r)]]) +
      (CFG.email ? "<p>" + reportLink(q) + "</p>" : "") + "</section>";
  }

  function mapHTML(list, current, cellClass) {
    return '<div class="map">' + list.map(function (q, i) {
      return '<button class="cell-q ' + cellClass(q) + (i === current ? " current" : "") + '" data-i="' + i + '" aria-label="Întrebarea ' + (i + 1) + '">' + (i + 1) + "</button>";
    }).join("") + "</div>";
  }

  /* ---------- Antrenament ---------- */
  function renderPractice() {
    var list = practiceList();
    if (!list.length) {
      app.innerHTML = '<article class="q"><p class="stem">Nu ai întrebări greșite.</p><p class="hint">Alege „Toate” sau un act normativ ca să continui.</p></article><aside class="rail"></aside>';
      return;
    }
    if (state.pIdx >= list.length) state.pIdx = list.length - 1;
    if (state.pIdx < 0) state.pIdx = 0;
    var q = list[state.pIdx];
    var perm = state.pPerm[q.id];
    var chosen = state.practice[q.id];
    var reveal = chosen !== undefined;
    var answered = ALL.filter(function (x) { return state.practice[x.id] !== undefined; });
    var right = answered.filter(function (x) { return state.practice[x.id] === x.c; }).length;

    app.innerHTML =
      '<article class="q">' +
        cartus([["Întrebarea", (state.pIdx + 1) + " / " + list.length], ["Act normativ", fmt(DOMAINS[q.d])]]) +
        '<p class="stem">' + fmt(q.q) + "</p>" +
        optionsHTML(q, perm, chosen, reveal) +
        (reveal ? noteHTML(q, perm, chosen) : '<p class="hint">Alege un răspuns. Pe calculator merg și tastele a–d sau 1–4.</p>') +
        '<nav class="pager"><button class="btn" id="p-prev"' + (state.pIdx === 0 ? " disabled" : "") + ">Înapoi</button>" +
        '<span class="count">' + (state.pIdx + 1) + " / " + list.length + "</span>" +
        '<button class="btn primary" id="p-next"' + (state.pIdx === list.length - 1 ? " disabled" : "") + ">Următoarea</button></nav>" +
      "</article>" +
      '<aside class="rail">' +
        '<section class="blk"><h2>Progres</h2><table class="stat"><tbody>' +
          "<tr><th>Rezolvate</th><td>" + answered.length + " / " + ALL.length + "</td></tr>" +
          "<tr><th>Corecte</th><td>" + right + "</td></tr>" +
          "<tr><th>Greșite</th><td>" + (answered.length - right) + "</td></tr>" +
          (state.best ? "<tr><th>Cea mai bună simulare</th><td>" + state.best.points + " / " + MAX_POINTS + "</td></tr>" : "") +
        "</tbody></table></section>" +
        '<section class="blk"><h2>Întrebări</h2>' + mapHTML(list, state.pIdx, function (x) {
          var a = state.practice[x.id];
          return a === undefined ? "" : (a === x.c ? "right" : "wrong");
        }) +
        '<p class="legend"><span class="lg-right">corectă</span><span class="lg-wrong">greșită</span></p>' +
        (state.confirmReset
          ? '<div class="confirm"><p>Ștergi tot progresul din antrenament?</p><div class="row"><button class="btn" id="p-reset-no">Nu</button><button class="btn primary" id="p-reset-yes">Da, șterge</button></div></div>'
          : '<button class="linklike" id="p-reset">Șterge progresul</button>') +
        "</section>" +
        (answered.length === ALL.length
          ? '<section class="blk"><h2>Ai rezolvat toate grilele de test</h2><p class="hint">Poți relua greșelile din filtrul „Greșite” sau poți face o simulare.</p></section>'
          : "") +
        waitlistHTML() +
      "</aside>";
  }

  function practiceAnswer(orig) {
    var list = practiceList();
    var q = list[state.pIdx];
    if (state.practice[q.id] !== undefined) return;
    state.practice[q.id] = orig;
    save();
    renderFilters();
    renderPractice();
  }

  /* ---------- Simulare ---------- */
  var tick = null;
  function startSim() {
    var order = shuffle(ALL.map(function (q) { return q.id; }));
    state.sim = { order: order, perm: perms(order), answers: {}, flags: {}, idx: 0, end: Date.now() + SIM_MINUTES * 60000, done: false, confirm: false };
    state.reviewAll = false;
    saveSim();
    startTick();
    render();
    window.scrollTo(0, 0);
  }
  function startTick() { clearInterval(tick); tick = setInterval(updateTimer, 1000); }
  function remaining() { return Math.max(0, Math.round((state.sim.end - Date.now()) / 1000)); }
  function clock(s) {
    var h = Math.floor(s / 3600), m = Math.floor((s % 3600) / 60), r = s % 60;
    return h + ":" + (m < 10 ? "0" : "") + m + ":" + (r < 10 ? "0" : "") + r;
  }
  function updateTimer() {
    if (!state.sim || state.sim.done) { clearInterval(tick); return; }
    var s = remaining();
    var el = document.getElementById("timer");
    if (el) { el.textContent = clock(s); el.classList.toggle("low", s < 300); }
    if (s <= 0) submitSim();
  }
  function submitSim() {
    var sim = state.sim;
    sim.done = true;
    sim.confirm = false;
    clearInterval(tick);
    var correct = sim.order.filter(function (id) { return sim.answers[id] === byId[id].c; }).length;
    sim.correct = correct;
    sim.points = Math.round(correct / sim.order.length * MAX_POINTS);
    if (!state.best || sim.points > state.best.points) { state.best = { points: sim.points }; save(); }
    saveSim();
    state.mode = "sim";
    render();
    window.scrollTo(0, 0);
  }

  function renderSimIntro() {
    var counts = {};
    ALL.forEach(function (q) { counts[q.d] = (counts[q.d] || 0) + 1; });
    var mix = Object.keys(DOMAINS).map(function (k) { return fmt(DOMAINS[k]) + " (" + counts[k] + ")"; }).join(", ");
    app.innerHTML =
      '<article class="q"><div class="intro">' +
        "<h2>Simulare de examen</h2>" +
        "<ol>" +
          "<li>Primești toate cele " + ALL.length + " de întrebări, în ordine aleatorie, cu variantele amestecate.</li>" +
          "<li>Ai " + SIM_MINUTES + " de minute, același ritm ca la examen. Când expiră timpul, lucrarea se predă singură.</li>" +
          "<li>Fiecare întrebare are un singur răspuns corect. Punctajul se raportează la " + MAX_POINTS + " de puncte, ca la examen. Promovezi de la " + PASS_POINTS + " de puncte, adică " + num(Math.ceil(PASS_POINTS / MAX_POINTS * ALL.length), "răspuns corect", "răspunsuri corecte") + " din " + ALL.length + ".</li>" +
          "<li>Răspunsurile corecte apar abia după predare. Poți marca întrebările la care vrei să revii.</li>" +
          "<li>Lucrarea se salvează pe acest dispozitiv. Dacă închizi pagina, continui de unde ai rămas, iar timpul curge mai departe.</li>" +
        "</ol>" +
        '<p class="hint">Distribuție: ' + mix + ".</p>" +
        '<div class="actions"><button class="btn primary" id="s-start">Începe simularea</button></div>' +
      "</div></article>" +
      '<aside class="rail"><section class="blk"><h2>Sfat</h2><p class="hint">Verifică în regulamentul sesiunii ce materiale sunt permise la examen. Dacă sunt permise, exersează cu documentația deschisă, ca să-ți măsori viteza de căutare.</p></section></aside>';
  }

  function firstUnanswered(sim) {
    for (var k = 1; k <= sim.order.length; k++) {
      var j = (sim.idx + k) % sim.order.length;
      if (sim.answers[sim.order[j]] === undefined) return j;
    }
    return -1;
  }

  function renderSimRun() {
    var sim = state.sim;
    var id = sim.order[sim.idx];
    var q = byId[id];
    var perm = sim.perm[id];
    var count = Object.keys(sim.answers).length;
    var flagged = Object.keys(sim.flags || {}).filter(function (k) { return sim.flags[k]; }).length;
    var list = sim.order.map(function (x) { return byId[x]; });
    var isFlag = !!(sim.flags && sim.flags[id]);
    app.innerHTML =
      '<article class="q">' +
        cartus([["Întrebarea", (sim.idx + 1) + " / " + sim.order.length], ["Timp rămas", clock(remaining()), "timer", "timer"], ["Act normativ", fmt(DOMAINS[q.d]), "", "", "span-sm"]]) +
        '<p class="stem">' + fmt(q.q) + "</p>" +
        optionsHTML(q, perm, sim.answers[id], false) +
        '<div class="actions"><button class="btn quiet" id="s-flag" aria-pressed="' + isFlag + '">' + (isFlag ? "Marcată pentru revizuire" : "Marchează pentru revizuire") + "</button></div>" +
        '<nav class="pager"><button class="btn" id="s-prev"' + (sim.idx === 0 ? " disabled" : "") + ">Înapoi</button>" +
        '<span class="count">' + (sim.idx + 1) + " / " + sim.order.length + "</span>" +
        '<button class="btn primary" id="s-next"' + (sim.idx === sim.order.length - 1 ? " disabled" : "") + ">Următoarea</button></nav>" +
      "</article>" +
      '<aside class="rail">' +
        '<section class="blk"><h2>Foaie de răspuns</h2>' + mapHTML(list, sim.idx, function (x) {
          return (sim.answers[x.id] !== undefined ? "answered" : "") + (sim.flags && sim.flags[x.id] ? " flagged" : "");
        }) +
        '<p class="legend"><span class="lg-ans">completată</span><span>necompletată</span><span class="lg-flag">marcată</span></p>' +
        '<table class="stat"><tbody><tr><th>Completate</th><td>' + count + " / " + sim.order.length + "</td></tr>" +
        "<tr><th>Marcate</th><td>" + flagged + "</td></tr></tbody></table>" +
        (count < sim.order.length ? '<button class="linklike" id="s-jump">Mergi la următoarea necompletată</button>' : "") +
        "</section>" +
        (sim.confirm
          ? '<div class="confirm"><p>Predai lucrarea' + (count < sim.order.length ? " cu " + num(sim.order.length - count, "întrebare necompletată", "întrebări necompletate") : "") + '?</p><div class="row"><button class="btn" id="s-cancel">Nu încă</button><button class="btn primary" id="s-submit">Predă</button></div></div>'
          : '<button class="btn" id="s-ask">Predă lucrarea</button>') +
      "</aside>";
    updateTimer();
  }

  function renderSimResults() {
    var sim = state.sim;
    var pass = sim.points >= PASS_POINTS;
    var byD = {};
    sim.order.forEach(function (id) {
      var q = byId[id];
      byD[q.d] = byD[q.d] || { n: 0, ok: 0 };
      byD[q.d].n++;
      if (sim.answers[id] === q.c) byD[q.d].ok++;
    });
    var rows = Object.keys(DOMAINS).filter(function (k) { return byD[k]; }).map(function (k) {
      return "<tr><td>" + fmt(DOMAINS[k]) + "</td><td>" + byD[k].ok + "</td><td>" + byD[k].n + "</td><td>" + Math.round(byD[k].ok / byD[k].n * 100) + "%</td></tr>";
    }).join("");
    var wrongCount = sim.order.filter(function (id) { return sim.answers[id] !== byId[id].c; }).length;
    var review = sim.order.map(function (id, i) {
      var q = byId[id];
      var perm = sim.perm[id];
      var a = sim.answers[id];
      var ok = a === q.c;
      if (ok && !state.reviewAll) return "";
      var yours = a === undefined
        ? '<p class="bad">Necompletată.</p>'
        : '<p class="' + (ok ? "good" : "bad") + '">Răspunsul tău: ' + letterOf(perm, a) + ") " + fmt(q.o[a]) + (ok ? ". Corect." : ". Greșit.") + "</p>";
      return '<li value="' + (i + 1) + '"><span class="src">' + fmt(DOMAINS[q.d]) + '</span><p class="stem">' + fmt(q.q) + "</p>" + yours +
        (ok ? "" : "<p>Răspuns corect: " + letterOf(perm, q.c) + ") " + fmt(q.o[q.c]) + "</p>") +
        "<p>" + fmt(q.e) + '</p><p class="ref"><b>Temei legal:</b> ' + fmt(q.r) + "</p>" +
        (CFG.email ? "<p>" + reportLink(q) + "</p>" : "") + "</li>";
    }).join("");
    app.innerHTML =
      '<article class="result">' +
        '<div class="score"><span class="big">' + sim.points + '</span><span class="of">din ' + MAX_POINTS + " de puncte</span></div>" +
        '<p class="verdict">Rezultat: <strong class="' + (pass ? "pass" : "fail") + '">' + (pass ? "admis" : "respins") + "</strong>. Ai " + num(sim.correct, "răspuns corect", "răspunsuri corecte") + " din " + sim.order.length + ". Pragul de promovare este de " + PASS_POINTS + " de puncte.</p>" +
        '<div class="tbl-wrap"><table class="tbl"><caption>Rezultate pe acte normative</caption>' +
          "<thead><tr><th>Act normativ</th><th>Corecte</th><th>Total</th><th>Procent</th></tr></thead>" +
          "<tbody>" + rows + "</tbody>" +
          "<tfoot><tr><td>Total</td><td>" + sim.correct + "</td><td>" + sim.order.length + "</td><td>" + Math.round(sim.correct / sim.order.length * 100) + "%</td></tr></tfoot>" +
        "</table></div>" +
        '<div class="actions"><button class="btn primary" id="s-again">Simulare nouă</button><button class="btn" id="s-practice">Exersează greșelile</button></div>' +
        '<div class="sec-head"><h2 class="sec-title">Fișa de corectare</h2><div class="seg" role="group" aria-label="Ce se afișează">' +
          '<button id="r-wrong" aria-pressed="' + !state.reviewAll + '">Greșite și necompletate (' + wrongCount + ")</button>" +
          '<button id="r-all" aria-pressed="' + state.reviewAll + '">Toate (' + sim.order.length + ")</button></div></div>" +
        (review ? '<ol class="review">' + review + "</ol>" : '<p class="hint">Nicio întrebare greșită.</p>') +
      "</article>" +
      '<aside class="rail"><section class="blk"><h2>Cum citești rezultatul</h2><p class="hint">Tabelul arată unde pierzi puncte. Fișa de corectare păstrează numerotarea din lucrare și dă temeiul legal pentru fiecare întrebare.</p></section>' +
      waitlistHTML() + "</aside>";
  }

  function render() {
    document.getElementById("mode-practice").setAttribute("aria-pressed", state.mode === "practice");
    document.getElementById("mode-sim").setAttribute("aria-pressed", state.mode === "sim");
    renderFilters();
    if (state.mode === "practice") renderPractice();
    else if (!state.sim) renderSimIntro();
    else if (state.sim.done) renderSimResults();
    else renderSimRun();
  }

  /* ---------- Evenimente ---------- */
  document.getElementById("mode-practice").addEventListener("click", function () { state.mode = "practice"; render(); });
  document.getElementById("mode-sim").addEventListener("click", function () { state.mode = "sim"; render(); });

  filters.addEventListener("click", function (ev) {
    var b = ev.target.closest("button");
    if (!b) return;
    state.filter = b.getAttribute("data-f");
    state.pIdx = 0;
    render();
  });

  app.addEventListener("click", function (ev) {
    var t = ev.target.closest("button");
    if (!t) return;
    var sim = state.sim;
    if (t.classList.contains("opt")) {
      var orig = parseInt(t.getAttribute("data-o"), 10);
      if (state.mode === "practice") practiceAnswer(orig);
      else if (sim && !sim.done) { sim.answers[sim.order[sim.idx]] = orig; saveSim(); renderSimRun(); }
      return;
    }
    if (t.classList.contains("cell-q")) {
      var i = parseInt(t.getAttribute("data-i"), 10);
      if (state.mode === "practice") { state.pIdx = i; renderPractice(); }
      else if (sim && !sim.done) { sim.idx = i; saveSim(); renderSimRun(); }
      return;
    }
    switch (t.id) {
      case "p-prev": state.pIdx--; renderPractice(); break;
      case "p-next": state.pIdx++; renderPractice(); break;
      case "p-reset": state.confirmReset = true; renderPractice(); break;
      case "p-reset-no": state.confirmReset = false; renderPractice(); break;
      case "p-reset-yes": state.practice = {}; state.pIdx = 0; state.confirmReset = false; save(); render(); break;
      case "s-start": case "s-again": startSim(); break;
      case "s-prev": sim.idx--; saveSim(); renderSimRun(); break;
      case "s-next": sim.idx++; saveSim(); renderSimRun(); break;
      case "s-flag":
        sim.flags = sim.flags || {};
        var cur = sim.order[sim.idx];
        if (sim.flags[cur]) delete sim.flags[cur]; else sim.flags[cur] = true;
        saveSim(); renderSimRun(); break;
      case "s-jump": var j = firstUnanswered(sim); if (j >= 0) { sim.idx = j; saveSim(); renderSimRun(); } break;
      case "s-ask": sim.confirm = true; renderSimRun(); break;
      case "s-cancel": sim.confirm = false; renderSimRun(); break;
      case "s-submit": submitSim(); break;
      case "r-wrong": state.reviewAll = false; renderSimResults(); break;
      case "r-all": state.reviewAll = true; renderSimResults(); break;
      case "s-practice":
        sim.order.forEach(function (id) { if (sim.answers[id] !== byId[id].c) delete state.practice[id]; });
        save();
        state.mode = "practice"; state.filter = "all"; state.pIdx = 0; render(); break;
    }
  });

  document.addEventListener("keydown", function (ev) {
    if (ev.target.closest && ev.target.closest("input, textarea, a")) return;
    if (ev.ctrlKey || ev.metaKey || ev.altKey) return;
    var k = ev.key.toLowerCase();
    var pos = ["a", "b", "c", "d"].indexOf(k);
    if (pos < 0) pos = ["1", "2", "3", "4"].indexOf(k);
    var running = state.mode === "sim" && state.sim && !state.sim.done;
    if (pos >= 0 && (state.mode === "practice" || running)) {
      var btns = app.querySelectorAll(".opt");
      if (btns[pos] && !btns[pos].disabled) btns[pos].click();
    } else if (k === "m" && running) {
      var f = document.getElementById("s-flag"); if (f) f.click();
    } else if (k === "arrowright") {
      var n = document.getElementById(state.mode === "practice" ? "p-next" : "s-next");
      if (n && !n.disabled) n.click();
    } else if (k === "arrowleft") {
      var p = document.getElementById(state.mode === "practice" ? "p-prev" : "s-prev");
      if (p && !p.disabled) p.click();
    }
  });

  if (state.sim && !state.sim.done) {
    if (remaining() <= 0) submitSim(); else startTick();
  }
  render();
})();
