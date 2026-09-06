"""The design system every rendered page shares.

One stylesheet, defined once, inlined into all four pages. The pages are self-contained
files that must work opened straight off disk with no server and no network — the operation
has been read that way since Brief 001 — so an external stylesheet is not an option and a
CDN font is not either.

**Palette provenance.** These tokens are the ones already in use in the last rendered
dashboard (``docs/reference/strategic-threat-briefing.frozen.html``, frozen at Brief 12).
Keeping them is a deliberate continuity decision: the rebuild changes how pages are
generated, not what the product looks like to someone who has been reading it for a month.
The one design question the migration left genuinely open — light theme (Briefs 001-011) vs
dark (Brief 012 and the dashboard) — is resolved here in favour of dark, so that the daily
brief and the standing picture stop being two visually unrelated products. See
``docs/REBUILD-NOTES.md``.

**Direction colour semantics.** ``escalating`` is red, ``easing`` green, ``holding`` steel
blue, ``volatile`` amber. Amber rather than a red/green blend is the point: ``volatile``
means large movement without a consistent direction, and a colour that reads as "halfway
between better and worse" would say the opposite of what the vocabulary means.
"""

from __future__ import annotations

__all__ = ["CSS", "DIRECTION_COLORS", "CATEGORY_COLORS", "EDGE_COLORS", "direction_color"]

#: Thread direction -> CSS custom property name.
DIRECTION_COLORS: dict[str, str] = {
    "escalating": "var(--dir-escalating)",
    "holding": "var(--dir-holding)",
    "easing": "var(--dir-easing)",
    "volatile": "var(--dir-volatile)",
}

#: ``map_nodes[].cat`` -> CSS custom property name.
CATEGORY_COLORS: dict[str, str] = {
    "home": "var(--blue)",
    "hemisphere": "var(--gold)",
    "adversary": "var(--red)",
    "ally": "var(--teal)",
    "contested": "var(--purple)",
    "terror": "var(--russia)",
}

#: ``node_edges[].type`` -> CSS custom property name.
EDGE_COLORS: dict[str, str] = {
    "alliance": "var(--blue)",
    "adversarial-cooperation": "var(--coop)",
    "conflict": "var(--red)",
    "contested": "var(--purple)",
    "hemisphere": "var(--gold)",
}


def direction_color(direction: str) -> str:
    """Colour for a thread direction, falling back to muted text for an unknown value.

    An unknown direction is a validator failure, not a renderer crash: the page still
    draws, in a colour that visibly does not belong, so the problem is seen rather than
    hidden behind a default that looks intentional.
    """
    return DIRECTION_COLORS.get(direction, "var(--dim)")


CSS = """
:root{
  --bg:#0A0D11; --panel:#12181F; --panel2:#161D26; --hair:#28323D;
  --text:#E8EDF2; --dim:#93A1B0; --faint:#63707E;
  --gold:#C6A15B; --red:#B5473B; --russia:#A15A3E; --iran:#8C3E4D;
  --nkorea:#705082; --blue:#4C7C97; --teal:#5FA0A6; --green:#74936B;
  --purple:#8574A0; --coop:#C08A46;
  --dir-escalating:#B5473B; --dir-holding:#4C7C97;
  --dir-easing:#74936B; --dir-volatile:#C6A15B;
  --radius:2px;
  --serif:"Iowan Old Style","Palatino Linotype",Palatino,Georgia,"Times New Roman",serif;
  --sans:ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
  --mono:ui-monospace,SFMono-Regular,"SF Mono",Menlo,Consolas,"Liberation Mono",monospace;
  color-scheme:dark;
}
*{box-sizing:border-box}
/* Several components below set an explicit `display`, which outranks the user-agent rule
   for [hidden]. Scripts toggle visibility with `el.hidden`, so this has to win. */
[hidden]{display:none!important}
html{-webkit-text-size-adjust:100%}
body{
  margin:0; background:var(--bg); color:var(--text);
  font-family:var(--sans); font-size:15px; line-height:1.6;
  -webkit-font-smoothing:antialiased;
}
a{color:var(--gold); text-decoration:none}
a:hover{text-decoration:underline}
h1,h2,h3,h4{margin:0; font-weight:600; line-height:1.2}
p{margin:0 0 0.9em}
p:last-child{margin-bottom:0}
hr{border:0; border-top:1px solid var(--hair); margin:32px 0}
code,.mono{font-family:var(--mono); font-size:0.88em}

.wrap{max-width:1180px; margin:0 auto; padding:0 24px}
.stack>*+*{margin-top:14px}

/* ---------- top bar ---------- */
.topbar{
  position:sticky; top:0; z-index:60;
  background:rgba(10,13,17,0.94); backdrop-filter:blur(8px);
  border-bottom:1px solid var(--hair);
}
.topbar .wrap{display:flex; align-items:center; gap:20px; height:52px}
.wordmark{
  font-family:var(--serif); font-size:15px; letter-spacing:0.02em;
  color:var(--text); white-space:nowrap;
}
.topbar nav{display:flex; gap:4px; margin-left:auto; flex-wrap:wrap}
.topbar nav a{
  color:var(--dim); font-size:12.5px; letter-spacing:0.06em;
  text-transform:uppercase; padding:6px 10px; border-radius:var(--radius);
}
.topbar nav a:hover{color:var(--text); background:var(--panel); text-decoration:none}
.topbar nav a.here{color:var(--gold); background:var(--panel)}

/* ---------- masthead ---------- */
.masthead{border-bottom:1px solid var(--hair); padding:44px 0 30px; background:var(--panel)}
.eyebrow-row{
  display:flex; gap:14px; flex-wrap:wrap;
  font-size:11px; letter-spacing:0.14em; text-transform:uppercase; color:var(--gold);
  margin-bottom:18px;
}
.eyebrow-row .dim{color:var(--faint)}
.masthead .title{font-family:var(--serif); font-size:clamp(30px,5vw,52px); letter-spacing:-0.01em}
.masthead .title .accent{color:var(--gold)}
.masthead .subtitle{
  margin-top:14px; max-width:74ch; color:var(--dim); font-size:15.5px;
}
.byline{
  display:flex; flex-wrap:wrap; gap:6px 26px; margin-top:22px;
  font-size:12.5px; color:var(--faint);
}
.byline b{color:var(--dim); font-weight:600}

/* ---------- stat strip ---------- */
.statstrip{
  display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr));
  border-bottom:1px solid var(--hair); background:var(--bg);
}
.statcell{padding:16px 20px; border-right:1px solid var(--hair)}
.statcell:last-child{border-right:0}
.statnum{font-family:var(--serif); font-size:26px; color:var(--gold); line-height:1}
.statlabel{margin-top:6px; font-size:11.5px; color:var(--faint); line-height:1.4}

/* ---------- sections ---------- */
section{padding:46px 0; border-bottom:1px solid var(--hair)}
section:last-of-type{border-bottom:0}
.sec-head{margin-bottom:26px}
.sec-eyebrow{
  font-size:11px; letter-spacing:0.16em; text-transform:uppercase;
  color:var(--gold); margin-bottom:10px;
}
.sec-title{font-family:var(--serif); font-size:clamp(22px,3vw,32px)}
.sec-desc{margin-top:12px; max-width:80ch; color:var(--dim); font-size:14.5px}

/* ---------- panels ---------- */
.panel{
  background:var(--panel); border:1px solid var(--hair);
  border-radius:var(--radius); padding:22px;
}
.panel.tight{padding:16px}
.grid{display:grid; gap:16px}
.grid.cols-2{grid-template-columns:repeat(auto-fit,minmax(300px,1fr))}
.grid.cols-3{grid-template-columns:repeat(auto-fit,minmax(260px,1fr))}

/* ---------- bottom line ---------- */
.bottomline{
  background:var(--panel); border:1px solid var(--hair);
  border-left:3px solid var(--gold);
  border-radius:var(--radius); padding:26px 28px;
}
.bottomline .bl-label{
  font-size:11px; letter-spacing:0.16em; text-transform:uppercase;
  color:var(--gold); margin-bottom:12px;
}
.bottomline .bl-text{
  font-family:var(--serif); font-size:clamp(16px,2vw,20px); line-height:1.55;
}

/* ---------- movement board ---------- */
.board{
  display:grid; grid-template-columns:repeat(10,1fr); gap:8px;
  background:var(--panel); border:1px solid var(--hair);
  border-radius:var(--radius); padding:20px 18px;
}
@media (max-width:820px){.board{grid-template-columns:repeat(5,1fr)}}
@media (max-width:420px){.board{grid-template-columns:repeat(2,1fr)}}
.gauge{display:flex; flex-direction:column; align-items:center; gap:8px; min-width:0}
.gauge .g-code{
  font-family:var(--mono); font-size:12px; letter-spacing:0.08em; color:var(--dim);
}
.gauge .g-bar{
  width:100%; height:104px; background:var(--panel2);
  border:1px solid var(--hair); border-radius:var(--radius);
  display:flex; align-items:flex-end; overflow:hidden;
}
.gauge .g-fill{width:100%; display:block}
.gauge .g-meta{display:flex; align-items:baseline; gap:5px}
.gauge .g-int{font-family:var(--serif); font-size:19px; line-height:1}
.gauge .g-arrow{font-size:12px; line-height:1}
.gauge .g-label{
  font-size:10.5px; color:var(--faint); text-align:center; line-height:1.3;
  overflow-wrap:anywhere;
}
.boardlegend{
  display:flex; gap:16px; flex-wrap:wrap; margin-top:12px;
  font-size:11.5px; color:var(--faint);
}
.boardlegend .lg{display:inline-flex; align-items:center; gap:6px}
.boardlegend .sw{width:10px; height:10px; border-radius:1px; display:inline-block}

/* ---------- thread detail rows ---------- */
.threadrow{
  border:1px solid var(--hair); border-radius:var(--radius);
  background:var(--panel); padding:16px 18px;
}
.threadrow+.threadrow{margin-top:10px}
.tr-head{display:flex; align-items:baseline; gap:10px; flex-wrap:wrap}
.tr-code{
  font-family:var(--mono); font-size:11px; letter-spacing:0.08em;
  border:1px solid var(--hair); border-radius:var(--radius); padding:2px 6px; color:var(--dim);
}
.tr-name{font-family:var(--serif); font-size:17px}
.tr-dir{
  font-size:11px; letter-spacing:0.1em; text-transform:uppercase; margin-left:auto;
}
.tr-one{margin-top:8px; color:var(--dim); font-size:14px}
.tr-status{margin-top:10px; font-size:13.5px; color:var(--faint); line-height:1.55}

/* ---------- cards ---------- */
.card{
  display:block; background:var(--panel); border:1px solid var(--hair);
  border-radius:var(--radius); padding:22px; color:inherit;
}
a.card:hover{border-color:var(--gold); text-decoration:none}
.card .c-eyebrow{
  font-size:11px; letter-spacing:0.14em; text-transform:uppercase; color:var(--gold);
}
.card .c-title{font-family:var(--serif); font-size:20px; margin-top:8px}
.card .c-desc{margin-top:10px; color:var(--dim); font-size:13.5px}
.card .c-stat{
  margin-top:16px; padding-top:14px; border-top:1px solid var(--hair);
  display:flex; align-items:baseline; gap:8px;
}
.card .c-statnum{font-family:var(--serif); font-size:24px; color:var(--text)}
.card .c-statlabel{font-size:11.5px; color:var(--faint)}

/* ---------- pills / tags ---------- */
.pill{
  display:inline-block; font-size:10.5px; letter-spacing:0.08em; text-transform:uppercase;
  border:1px solid var(--hair); border-radius:999px; padding:2px 9px; color:var(--dim);
  white-space:nowrap;
}
.pill.tier-verified-primary{border-color:var(--green); color:var(--green)}
.pill.tier-attributed-claim{border-color:var(--gold); color:var(--gold)}
.pill.tier-contested{border-color:var(--red); color:var(--red)}
.pill.tier-single-source{border-color:var(--purple); color:var(--purple)}
.pill.tier-analyst-judgment{border-color:var(--blue); color:var(--blue)}
.pill.tier-reference{border-color:var(--faint); color:var(--faint)}
.pill.late{border-color:var(--red); color:var(--red)}

/* ---------- filter bar ---------- */
.filterbar{display:flex; flex-wrap:wrap; gap:6px; margin-bottom:18px}
.fbtn{
  font:inherit; font-size:12px; letter-spacing:0.04em; cursor:pointer;
  background:var(--panel); color:var(--dim);
  border:1px solid var(--hair); border-radius:var(--radius); padding:5px 11px;
}
.fbtn:hover{color:var(--text); border-color:var(--dim)}
.fbtn[aria-pressed="true"]{background:var(--gold); border-color:var(--gold); color:#12181F}
.togglewrap{display:flex; align-items:center; gap:10px; margin:6px 0 20px; font-size:13px; color:var(--dim)}
.switch{
  width:38px; height:20px; border-radius:999px; background:var(--panel2);
  border:1px solid var(--hair); position:relative; cursor:pointer; flex:none;
}
.switch .knob{
  position:absolute; top:2px; left:2px; width:14px; height:14px; border-radius:50%;
  background:var(--faint); transition:left .15s, background .15s;
}
.switch[aria-pressed="true"]{background:rgba(198,161,91,0.2); border-color:var(--gold)}
.switch[aria-pressed="true"] .knob{left:20px; background:var(--gold)}

/* ---------- timeline rail ---------- */
.rail{border-left:1px solid var(--hair); padding-left:22px; margin-left:6px}
.event{position:relative; padding:0 0 24px}
.event::before{
  content:""; position:absolute; left:-27px; top:7px;
  width:9px; height:9px; border-radius:50%;
  background:var(--bg); border:1px solid var(--dim);
}
.event.is-future::before{border-style:dashed; border-color:var(--gold)}
.event .e-date{
  font-family:var(--mono); font-size:11.5px; letter-spacing:0.06em; color:var(--gold);
}
.event .e-title{font-family:var(--serif); font-size:17px; margin-top:4px}
.event .e-text{margin-top:6px; color:var(--dim); font-size:13.5px; max-width:82ch}
.event .e-meta{margin-top:8px; display:flex; gap:8px; flex-wrap:wrap; align-items:center}
.event.is-future .e-title{color:var(--gold)}
.emptystate{color:var(--faint); font-size:13.5px; padding:18px 0}

/* ---------- briefings accordion ---------- */
.briefing{
  border:1px solid var(--hair); border-radius:var(--radius);
  background:var(--panel); margin-bottom:8px;
}
.briefing summary{
  cursor:pointer; padding:15px 18px; display:flex; align-items:center;
  gap:12px; list-style:none;
}
.briefing summary::-webkit-details-marker{display:none}
.briefing .b-index{
  font-family:var(--mono); font-size:11px; color:var(--faint); margin-right:4px;
}
.briefing .b-title{font-family:var(--serif); font-size:17px}
.briefing .b-chevron{margin-left:auto; color:var(--faint); font-size:15px}
.briefing[open] .b-chevron{color:var(--gold)}
.briefing .b-body{
  padding:2px 18px 20px; border-top:1px solid var(--hair);
  color:var(--dim); font-size:14px; line-height:1.65;
}
.briefing .b-body strong{color:var(--text); font-weight:600}
.briefing .b-body ul{margin:0 0 1em; padding-left:20px}
.briefing .b-body li{margin-bottom:6px}
.briefing .b-body .ol-label{
  font-size:11px; letter-spacing:0.14em; text-transform:uppercase;
  color:var(--gold); margin:14px 0 6px;
}

/* ---------- tables ---------- */
.table{width:100%; border-collapse:collapse; font-size:13.5px}
.table th,.table td{
  text-align:left; padding:10px 12px; border-bottom:1px solid var(--hair);
  vertical-align:top;
}
.table th{
  font-size:11px; letter-spacing:0.1em; text-transform:uppercase;
  color:var(--faint); font-weight:600;
}
.table td{color:var(--dim)}
.table td b,.table td strong{color:var(--text)}
.tablewrap{overflow-x:auto; -webkit-overflow-scrolling:touch}

/* ---------- map ---------- */
.mapbox{
  position:relative; background:var(--panel); border:1px solid var(--hair);
  border-radius:var(--radius); aspect-ratio:1000/460; min-height:300px; overflow:hidden;
}
.mapbox svg{position:absolute; inset:0; width:100%; height:100%}
.node{cursor:pointer}
.node circle{transition:r .12s, stroke-width .12s}
.node:hover circle,.node[aria-current="true"] circle{stroke:var(--text); stroke-width:2}
.node text{
  font-family:var(--sans); font-size:9px; letter-spacing:0.05em;
  fill:var(--dim); pointer-events:none; text-anchor:middle;
}
.node:hover text{fill:var(--text)}
.maplegend{display:flex; flex-wrap:wrap; gap:14px; margin-bottom:14px; font-size:11.5px; color:var(--faint)}
.maplegend .lg{display:inline-flex; align-items:center; gap:6px}
.maplegend .dot{width:9px; height:9px; border-radius:50%; display:inline-block}
.mappanel{
  margin-top:14px; background:var(--panel); border:1px solid var(--hair);
  border-left:3px solid var(--gold); border-radius:var(--radius); padding:18px 20px;
}
.mappanel .mp-label{
  font-size:11px; letter-spacing:0.14em; text-transform:uppercase; color:var(--gold);
}
.mappanel h4{font-family:var(--serif); font-size:19px; margin-top:6px}
.mappanel p{margin-top:8px; color:var(--dim); font-size:13.5px}

/* ---------- deep dive (node map) ---------- */
.dive{display:grid; gap:18px; grid-template-columns:minmax(0,1fr)}
@media (min-width:960px){.dive{grid-template-columns:minmax(0,1.15fr) minmax(0,1fr)}}
.divecol h5{
  font-size:11px; letter-spacing:0.14em; text-transform:uppercase;
  color:var(--gold); margin-bottom:12px;
}
.diveitem{border-left:1px solid var(--hair); padding:0 0 16px 16px; position:relative}
.diveitem::before{
  content:""; position:absolute; left:-4px; top:7px; width:7px; height:7px;
  border-radius:50%; background:var(--faint);
}
.diveitem .di-date{font-family:var(--mono); font-size:11px; color:var(--gold)}
.diveitem .di-ago{color:var(--faint); margin-left:6px}
.diveitem .di-title{font-family:var(--serif); font-size:15.5px; margin-top:3px}
.diveitem .di-text{margin-top:5px; color:var(--dim); font-size:13px}
.diveitem .di-src{margin-top:6px; font-size:11.5px; color:var(--faint)}

/* ---------- archive ---------- */
.digestbar{
  display:flex; flex-wrap:wrap; gap:16px; align-items:flex-end;
  background:var(--panel); border:1px solid var(--hair);
  border-radius:var(--radius); padding:18px 20px; margin-bottom:22px;
}
.field{display:flex; flex-direction:column; gap:6px}
.field label{font-size:11px; letter-spacing:0.1em; text-transform:uppercase; color:var(--faint)}
.field input,.field select{
  font:inherit; font-size:13px; background:var(--panel2); color:var(--text);
  border:1px solid var(--hair); border-radius:var(--radius); padding:7px 10px;
}
.digestout{margin-bottom:26px}
.briefcard{
  background:var(--panel); border:1px solid var(--hair);
  border-radius:var(--radius); padding:20px 22px; margin-bottom:12px;
}
.briefcard .bc-head{display:flex; align-items:baseline; gap:12px; flex-wrap:wrap}
.briefcard .bc-num{font-family:var(--mono); font-size:12px; color:var(--gold)}
.briefcard .bc-date{font-family:var(--serif); font-size:19px}
.briefcard .bc-cutoff{font-family:var(--mono); font-size:11.5px; color:var(--faint); margin-left:auto}
.briefcard .bc-bl{margin-top:12px; font-size:14px; color:var(--dim); line-height:1.6}
.briefcard .bc-items{margin-top:14px; border-top:1px solid var(--hair); padding-top:14px}
.bc-item{padding:9px 0; border-bottom:1px dotted var(--hair)}
.bc-item:last-child{border-bottom:0}
.bc-item .bi-head{display:flex; gap:9px; align-items:baseline; flex-wrap:wrap}
.bc-item .bi-n{font-family:var(--mono); font-size:11px; color:var(--faint); flex:none}
.bc-item .bi-title{font-size:14px; color:var(--text)}
.bc-item .bi-sowhat{margin-top:5px; font-size:13px; color:var(--dim); padding-left:26px}
.bc-strip{display:flex; flex-wrap:wrap; gap:5px; margin-top:14px}
.chip{
  font-family:var(--mono); font-size:10.5px; letter-spacing:0.04em;
  border:1px solid var(--hair); border-radius:var(--radius); padding:2px 7px; color:var(--dim);
}
.chip.moved{border-color:var(--gold); color:var(--gold)}
.notice{
  background:rgba(181,71,59,0.08); border:1px solid var(--red);
  border-radius:var(--radius); padding:14px 18px; color:var(--text); font-size:13.5px;
}
.notice .n-label{
  font-size:11px; letter-spacing:0.14em; text-transform:uppercase; color:var(--red);
  margin-bottom:6px;
}

/* ---------- footer ---------- */
footer{padding:40px 0 60px; color:var(--faint); font-size:12.5px}
footer .gen{margin-top:18px; font-family:var(--mono); font-size:11px; color:var(--faint)}

@media print{
  .topbar,.filterbar,.togglewrap,.digestbar{display:none}
  body{background:#fff; color:#000}
  .panel,.card,.briefcard,.bottomline{border-color:#ccc; background:#fff}
}
"""
