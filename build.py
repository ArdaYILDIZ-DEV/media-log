import os
import re
import json
import shutil
from datetime import datetime

# ── helpers ──────────────────────────────────────────────────────────────────

def parse_frontmatter(text):
    """Extract YAML frontmatter and body from markdown."""
    meta = {}
    body = text
    m = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)', text, re.DOTALL)
    if m:
        for line in m.group(1).splitlines():
            if ':' in line:
                k, _, v = line.partition(':')
                meta[k.strip()] = v.strip()
        body = m.group(2)
    return meta, body

def md_to_html(text):
    """Minimal markdown → HTML (headings, lists, paragraphs, inline)."""
    lines = text.split('\n')
    html = []
    in_ul = False

    def close_ul():
        nonlocal in_ul
        if in_ul:
            html.append('</ul>')
            in_ul = False

    def inline(s):
        s = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)
        s = re.sub(r'\*(.+?)\*',     r'<em>\1</em>', s)
        s = re.sub(r'`(.+?)`',       r'<code>\1</code>', s)
        return s

    for line in lines:
        if re.match(r'^#{1,6}\s', line):
            close_ul()
            level = len(re.match(r'^(#+)', line).group(1))
            content = inline(line.lstrip('#').strip())
            html.append(f'<h{level}>{content}</h{level}>')
        elif line.startswith('- ') or line.startswith('* '):
            if not in_ul:
                html.append('<ul>')
                in_ul = True
            html.append(f'<li>{inline(line[2:])}</li>')
        elif line.strip() == '':
            close_ul()
            html.append('')
        else:
            close_ul()
            html.append(f'<p>{inline(line)}</p>')

    close_ul()
    return '\n'.join(html)

def slug(filename):
    return os.path.splitext(filename)[0]

TR_MONTHS = {
    1:'Oca', 2:'Şub', 3:'Mar', 4:'Nis', 5:'May', 6:'Haz',
    7:'Tem', 8:'Ağu', 9:'Eyl', 10:'Eki', 11:'Kas', 12:'Ara'
}

def format_date(d):
    try:
        dt = datetime.strptime(d, '%Y-%m-%d')
        return f"{dt.day:02d} {TR_MONTHS[dt.month]} {dt.year}"
    except:
        return d

# ── CSS + layout ──────────────────────────────────────────────────────────────

CSS = """
@import url('https://fonts.googleapis.com/css2?family=EB+Garamond:ital,wght@0,400;0,500;1,400&family=DM+Mono:wght@400;500&display=swap');

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

:root {
  --bg:      #0e0e0e;
  --surface: #161616;
  --border:  #2a2a2a;
  --text:    #d4cfc8;
  --muted:   #6b6560;
  --accent:  #c8a97e;
  --anime:   #7eb8c8;
  --film:    #c87e9a;
  --show:    #9ac87e;
}

html { font-size: 16px; }

body {
  font-family: 'EB Garamond', Georgia, serif;
  background: var(--bg);
  color: var(--text);
  min-height: 100vh;
  line-height: 1.7;
}

a { color: inherit; text-decoration: none; }

/* ── header ── */
header {
  border-bottom: 1px solid var(--border);
  padding: 2rem 0 1.5rem;
  margin-bottom: 3rem;
}
.header-inner {
  max-width: 960px;
  margin: 0 auto;
  padding: 0 1.5rem;
  display: flex;
  align-items: baseline;
  gap: 1rem;
}
.site-title {
  font-family: 'DM Mono', monospace;
  font-size: 0.85rem;
  color: var(--accent);
  letter-spacing: 0.08em;
  text-transform: uppercase;
}
.site-subtitle {
  font-size: 0.9rem;
  color: var(--muted);
  font-style: italic;
}

/* ── main container ── */
.container {
  max-width: 960px;
  margin: 0 auto;
  padding: 0 1.5rem 5rem;
}

/* ── search ── */
.search-wrap {
  margin-bottom: 1rem;
}
.search-input {
  width: 100%;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 3px;
  padding: 0.6rem 0.9rem;
  font-family: 'DM Mono', monospace;
  font-size: 0.78rem;
  color: var(--text);
  outline: none;
  transition: border-color 0.15s;
  letter-spacing: 0.02em;
}
.search-input::placeholder { color: var(--muted); }
.search-input:focus { border-color: var(--accent); }

/* ── filters ── */
.filters {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
  margin-bottom: 1.5rem;
  align-items: center;
}
.filter-btn {
  font-family: 'DM Mono', monospace;
  font-size: 0.68rem;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  padding: 0.3rem 0.7rem;
  border-radius: 2px;
  border: 1px solid var(--border);
  background: transparent;
  color: var(--muted);
  cursor: pointer;
  transition: all 0.15s;
}
.filter-btn:hover {
  border-color: var(--accent);
  color: var(--text);
}
.filter-btn.active {
  border-color: var(--accent);
  color: var(--accent);
  background: #c8a97e10;
}
.filter-divider {
  width: 1px;
  height: 1rem;
  background: var(--border);
  margin: 0 0.2rem;
}

/* ── section label ── */
.section-label {
  font-family: 'DM Mono', monospace;
  font-size: 0.7rem;
  color: var(--muted);
  letter-spacing: 0.12em;
  text-transform: uppercase;
  margin-bottom: 1.25rem;
}

/* ── poster grid ── */
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 8px;
}

.poster-card {
  position: relative;
  cursor: pointer;
  overflow: hidden;
  border-radius: 3px;
  background: var(--surface);
  border: 1px solid var(--border);
  transition: border-color 0.15s, transform 0.15s;
  display: block;
}
.poster-card:hover {
  border-color: var(--accent);
  transform: translateY(-4px) scale(1.03);
  box-shadow: 0 12px 30px rgba(0,0,0,0.35);
  z-index: 10;
}
.poster-card:hover .date-badge {
  opacity: 1;
}

.poster-img {
  width: 100%;
  aspect-ratio: 2/3;
  display: block;
  background-size: cover;
  background-position: center top;
  background-color: #1a1a1a;
  position: relative;
}
.poster-img::after {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(to top, rgba(14,14,14,0.95) 0%, rgba(14,14,14,0.35) 45%, transparent 70%);
}

.no-poster-img {
  width: 100%;
  aspect-ratio: 2/3;
  background: var(--surface);
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: 'DM Mono', monospace;
  font-size: 2rem;
  color: var(--border);
  position: relative;
}
.no-poster-img::after {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(to top, rgba(22,22,22,0.98) 0%, rgba(22,22,22,0.4) 45%, transparent 70%);
}

.poster-overlay {
  position: absolute;
  bottom: 0; left: 0; right: 0;
  padding: 0.6rem 0.65rem;
  z-index: 1;
}
.poster-title {
  font-size: 0.91rem;
  font-weight: 500;
  color: #e8e3db;
  letter-spacing: 0.2px;
  line-height: 1.25;
  margin-bottom: 0.3rem;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.poster-meta {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  flex-wrap: wrap;
}

.tag {
  font-family: 'DM Mono', monospace;
  font-size: 0.58rem;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  padding: 0.1rem 0.35rem;
  border-radius: 2px;
}
.tag-anime { background: rgba(126,184,200,0.12); color: var(--anime); border: 1px solid rgba(126,184,200,0.25); }
.tag-film  { background: rgba(200,126,154,0.12); color: var(--film);  border: 1px solid rgba(200,126,154,0.25); }
.tag-show  { background: rgba(154,200,126,0.12); color: var(--show);  border: 1px solid rgba(154,200,126,0.25); }

.entry-score {
  font-family: 'DM Mono', monospace;
  font-size: 0.65rem;
  color: var(--accent);
}

.entry-score::before {
  content: "★";
  margin-right: 4px;
  color: var(--accent);
  font-size: 0.93rem;
}

.status-dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  flex-shrink: 0;
}
.dot-watching { background: #a78ee6; }
.dot-finished { background: #7ec89a; }
.dot-dropped  { background: #c87e7e; }
.dot-planned  { background: var(--muted); }

.date-badge {
  position: absolute;
  top: 0.5rem; right: 0.5rem;
  font-family: 'DM Mono', monospace;
  font-size: 0.6rem;
  color: var(--muted);
  background: rgba(14,14,14,0.82);
  border: 1px solid var(--border);
  padding: 0.15rem 0.4rem;
  border-radius: 2px;
  z-index: 2;
  opacity: 0;
  transition: opacity 0.15s;
  white-space: nowrap;
  letter-spacing: 0.03em;
}

/* ── entry page ── */
.back-link {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  font-family: 'DM Mono', monospace;
  font-size: 0.72rem;
  color: var(--muted);
  letter-spacing: 0.06em;
  text-transform: uppercase;
  margin-bottom: 2.5rem;
  transition: color 0.15s;
}
.back-link:hover { color: var(--accent); }

.entry-header { margin-bottom: 2rem; }
.entry-header h1 {
  font-size: 2rem;
  font-weight: 500;
  line-height: 1.2;
  margin-bottom: 0.75rem;
  color: #e8e3db;
}
.entry-attrs {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem 1.25rem;
  font-family: 'DM Mono', monospace;
  font-size: 0.72rem;
  color: var(--muted);
}
.entry-attrs span { display: flex; gap: 0.35rem; }
.entry-attrs .key { color: var(--muted); }
.entry-attrs .val { color: var(--text); }

.divider {
  border: none;
  border-top: 1px solid var(--border);
  margin: 2rem 0;
}

/* ── markdown body ── */
.entry-body h2 {
  font-size: 0.72rem;
  font-family: 'DM Mono', monospace;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--muted);
  margin: 2rem 0 0.75rem;
}
.entry-body h3 {
  font-size: 1rem;
  font-weight: 500;
  margin: 1.25rem 0 0.4rem;
  color: var(--text);
}
.entry-body p {
  margin-bottom: 0.75rem;
  color: var(--text);
  font-size: 1.05rem;
}
.entry-body ul {
  padding-left: 1.25rem;
  margin-bottom: 0.75rem;
}
.entry-body li {
  color: var(--text);
  margin-bottom: 0.2rem;
  font-size: 1.05rem;
}
.entry-body code {
  font-family: 'DM Mono', monospace;
  font-size: 0.85em;
  background: #1f1f1f;
  padding: 0.1em 0.35em;
  border-radius: 2px;
  color: var(--accent);
}
.entry-body strong { color: #e8e3db; }

/* ── poster (entry page) ── */
.entry-header-with-poster {
  display: grid;
  grid-template-columns: 1fr 140px;
  gap: 1.5rem;
  align-items: start;
}
.entry-poster {
  width: 140px;
  aspect-ratio: 2/3;
  border-radius: 3px;
  border: 1px solid var(--border);
  background-size: cover;
  background-position: center;
  background-color: var(--surface);
}

/* ── responsive ── */
@media (max-width: 600px) {
  .entry-header h1 { font-size: 1.5rem; }
  .entry-header-with-poster { grid-template-columns: 1fr; }
  .entry-poster { width: 100px; order: -1; }
  .grid { grid-template-columns: repeat(auto-fill, minmax(120px, 1fr)); }
}
"""

def base_html(title, body):
    return f"""<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>{CSS}</style>
</head>
<body>
<header>
  <div class="header-inner">
    <a class="site-title" href="/media-log/index.html">media-log</a>
    <span class="site-subtitle">film, anime, dizi notları</span>
  </div>
</header>
{body}
</body>
</html>"""

# ── build ─────────────────────────────────────────────────────────────────────

CATEGORIES = ['animes', 'films', 'shows']
OUT = '_site'

if os.path.exists(OUT):
    shutil.rmtree(OUT)
os.makedirs(OUT)

for cat in CATEGORIES:
    os.makedirs(f'{OUT}/{cat}', exist_ok=True)

all_entries = []

for cat in CATEGORIES:
    if not os.path.isdir(cat):
        continue
    for fname in os.listdir(cat):
        if not fname.endswith('.md'):
            continue
        with open(f'{cat}/{fname}', encoding='utf-8') as f:
            raw = f.read()

        meta, body = parse_frontmatter(raw)
        s = slug(fname)
        entry_type = meta.get('type', cat.rstrip('s').capitalize())
        tag_class = f"tag-{entry_type.lower()}"

        attrs_html = ''
        for key in ['year', 'studio', 'score', 'status', 'date']:
            val = meta.get(key)
            if val:
                label = 'added' if key == 'date' else key
                display = format_date(val) if key == 'date' else val
                attrs_html += f'<span><span class="key">{label}</span><span class="val">{display}</span></span>\n'

        poster = meta.get('poster', '')
        if poster:
            header_html = f'''<div class="entry-header-with-poster">
  <div class="entry-header">
    <h1>{meta.get('title', s)}</h1>
    <div class="entry-attrs">
      <span><span class="key">type</span><span class="val"><span class="tag {tag_class}">{entry_type}</span></span></span>
      {attrs_html}
    </div>
  </div>
  <div class="entry-poster" style="background-image:url('{poster}')"></div>
</div>'''
        else:
            header_html = f'''<div class="entry-header">
  <h1>{meta.get('title', s)}</h1>
  <div class="entry-attrs">
    <span><span class="key">type</span><span class="val"><span class="tag {tag_class}">{entry_type}</span></span></span>
    {attrs_html}
  </div>
</div>'''

        content = f"""
<div class="container">
  <a class="back-link" href="/media-log/index.html">← back</a>
  {header_html}
  <hr class="divider">
  <div class="entry-body">{md_to_html(body)}</div>
</div>"""

        page = base_html(meta.get('title', s), content)
        with open(f'{OUT}/{cat}/{s}.html', 'w', encoding='utf-8') as f:
            f.write(page)

        all_entries.append({
            'title':     meta.get('title', s),
            'type':      entry_type,
            'score':     meta.get('score', ''),
            'status':    meta.get('status', ''),
            'date':      meta.get('date', ''),
            'date_fmt':  format_date(meta.get('date', '')),
            'url':       f'{cat}/{s}.html',
            'tag_class': tag_class,
            'year':      meta.get('year', ''),
            'studio':    meta.get('studio', ''),
            'poster':    poster,
        })

all_entries.sort(key=lambda e: e['date'], reverse=True)

# ── index page (poster grid) ──────────────────────────────────────────────────

TYPE_ICON = {'anime': '◈', 'film': '▣', 'show': '◉'}

cards = ''
for e in all_entries:
    t        = e['type'].lower()
    st       = e['status'].lower()
    is_planned = st == 'planned'
    score_html = '' if is_planned else (f'<span class="entry-score">{e["score"]}</span>' if e['score'] else '')
    dot_class  = f'dot-{st}' if st in ('watching','finished','dropped','planned') else 'dot-planned'
    tag_html   = f'<span class="tag {e["tag_class"]}">{e["type"]}</span>'
    dot_html   = f'<span class="status-dot {dot_class}"></span>'
    date_badge = f'<span class="date-badge">{e["date_fmt"]}</span>'
    overlay    = f'''<div class="poster-overlay">
      <div class="poster-title">{e["title"]}</div>
      <div class="poster-meta">{tag_html}{dot_html}{score_html}</div>
    </div>'''

    if e['poster']:
        inner = f'<div class="poster-img" style="background-image:url(\'{e["poster"]}\')"></div>'
    else:
        icon  = TYPE_ICON.get(t, '◇')
        inner = f'<div class="no-poster-img">{icon}</div>'

    cards += f'''
<a href="{e['url']}" class="poster-card"
   data-type="{t}" data-status="{st}"
   data-title="{e['title'].lower()}"
   data-score="{e['score'].replace('/10','').strip()}"
   data-year="{e.get('year','')}"
   data-studio="{e.get('studio','').lower()}">
  {date_badge}
  {inner}
  {overlay}
</a>'''

index_body = f"""
<div class="container">
  <div class="search-wrap">
    <input class="search-input" type="text" placeholder="search... (score:9, year:2019, studio:mappa)">
  </div>
  <div class="filters">
    <button class="filter-btn active" data-filter="all">All</button>
    <button class="filter-btn" data-filter="anime">Anime</button>
    <button class="filter-btn" data-filter="film">Film</button>
    <button class="filter-btn" data-filter="show">Show</button>
    <span class="filter-divider"></span>
    <button class="filter-btn" data-filter="watching">Watching</button>
    <button class="filter-btn" data-filter="finished">Finished</button>
    <button class="filter-btn" data-filter="dropped">Dropped</button>
    <button class="filter-btn" data-filter="planned">Planned</button>
  </div>
  <div class="section-label">recent entries — <span id="count">{len(all_entries)}</span> total</div>
  <div class="grid">{cards}
  </div>
</div>
<script>
const btns  = document.querySelectorAll('.filter-btn');
const cards = document.querySelectorAll('.poster-card');
const searchInput = document.querySelector('.search-input');
let activeFilter = 'all';

function applyFilters() {{
  const raw = searchInput.value.trim().toLowerCase();
  let titleQ = '', scoreQ = '', yearQ = '', studioQ = '';
  if (raw) {{
    const scoreM  = raw.match(/score:([^ ]+)/);
    const yearM   = raw.match(/year:([^ ]+)/);
    const studioM = raw.match(/studio:([^ ]+)/);
    if (scoreM)  scoreQ  = scoreM[1];
    if (yearM)   yearQ   = yearM[1];
    if (studioM) studioQ = studioM[1];
    titleQ = raw.replace(/score:[^ ]+/g,'').replace(/year:[^ ]+/g,'').replace(/studio:[^ ]+/g,'').trim();
  }}

  let visible = 0;
  cards.forEach(card => {{
    const type   = card.dataset.type;
    const status = card.dataset.status;
    const title  = card.dataset.title  || '';
    const score  = card.dataset.score  || '';
    const year   = card.dataset.year   || '';
    const studio = card.dataset.studio || '';

    const filterOk = activeFilter === 'all' || type === activeFilter || status === activeFilter;
    const titleOk  = !titleQ  || title.includes(titleQ);
    const scoreOk  = !scoreQ  || score === scoreQ;
    const yearOk   = !yearQ   || year === yearQ;
    const studioOk = !studioQ || studio.includes(studioQ);

    const show = filterOk && titleOk && scoreOk && yearOk && studioOk;
    card.style.display = show ? '' : 'none';
    if (show) visible++;
  }});

  document.getElementById('count').textContent = visible;
}}

btns.forEach(btn => {{
  btn.addEventListener('click', () => {{
    btns.forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    activeFilter = btn.dataset.filter;
    applyFilters();
  }});
}});

searchInput.addEventListener('input', applyFilters);
</script>"""

with open(f'{OUT}/index.html', 'w', encoding='utf-8') as f:
    f.write(base_html('media-log', index_body))

print(f"✓ built {len(all_entries)} entries → {OUT}/")
