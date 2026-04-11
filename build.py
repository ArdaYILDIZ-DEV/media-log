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
    """Markdown → HTML with extended support."""
    lines = text.split('\n')
    html = []
    in_ul = False
    in_ol = False
    in_blockquote = False
    ol_counter = 0

    def close_ul():
        nonlocal in_ul
        if in_ul:
            html.append('</ul>')
            in_ul = False

    def close_ol():
        nonlocal in_ol, ol_counter
        if in_ol:
            html.append('</ol>')
            in_ol = False
            ol_counter = 0

    def close_blockquote():
        nonlocal in_blockquote
        if in_blockquote:
            html.append('</blockquote>')
            in_blockquote = False

    def close_all():
        close_ul()
        close_ol()
        close_blockquote()

    def inline(s):
        # links
        s = re.sub(r'\[(.+?)\]\((https?://[^\)]+)\)', r'<a href="\2" target="_blank" rel="noopener">\1</a>', s)
        # bold+italic
        s = re.sub(r'\*\*\*(.+?)\*\*\*', r'<strong><em>\1</em></strong>', s)
        # bold
        s = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)
        # italic
        s = re.sub(r'\*(.+?)\*', r'<em>\1</em>', s)
        # strikethrough
        s = re.sub(r'~~(.+?)~~', r'<del>\1</del>', s)
        # inline code
        s = re.sub(r'`(.+?)`', r'<code>\1</code>', s)
        return s

    i = 0
    while i < len(lines):
        line = lines[i]

        # horizontal rule
        if re.match(r'^[-*_]{3,}\s*$', line):
            close_all()
            html.append('<hr class="md-hr">')
            i += 1
            continue

        # headings
        if re.match(r'^#{1,6}\s', line):
            close_all()
            level = len(re.match(r'^(#+)', line).group(1))
            content = inline(line.lstrip('#').strip())
            html.append(f'<h{level}>{content}</h{level}>')
            i += 1
            continue

        # blockquote
        if line.startswith('> '):
            close_ul()
            close_ol()
            if not in_blockquote:
                html.append('<blockquote>')
                in_blockquote = True
            html.append(f'<p>{inline(line[2:])}</p>')
            i += 1
            continue
        elif in_blockquote and line.strip() == '':
            close_blockquote()
            i += 1
            continue

        # unordered list
        if re.match(r'^[-*+] ', line):
            close_ol()
            close_blockquote()
            if not in_ul:
                html.append('<ul>')
                in_ul = True
            # nested check
            content = line[2:]
            html.append(f'<li>{inline(content)}</li>')
            i += 1
            continue

        # ordered list
        if re.match(r'^\d+\. ', line):
            close_ul()
            close_blockquote()
            if not in_ol:
                html.append('<ol>')
                in_ol = True
            content = re.sub(r'^\d+\. ', '', line)
            html.append(f'<li>{inline(content)}</li>')
            i += 1
            continue

        # fenced code block
        if line.startswith('```'):
            close_all()
            lang = line[3:].strip()
            lang_class = f' class="language-{lang}"' if lang else ''
            code_lines = []
            i += 1
            while i < len(lines) and not lines[i].startswith('```'):
                code_lines.append(lines[i])
                i += 1
            code = '\n'.join(code_lines)
            # escape HTML inside code blocks
            code = code.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            html.append(f'<pre><code{lang_class}>{code}</code></pre>')
            i += 1
            continue

        # blank line
        if line.strip() == '':
            close_all()
            html.append('')
            i += 1
            continue

        # paragraph
        close_all()
        html.append(f'<p>{inline(line)}</p>')
        i += 1

    close_all()
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

html { font-size: 16px; zoom: 1.2; }

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

/* ── improved gradient overlay for readability ── */
.poster-img::after {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(
    to top,
    rgba(10,10,10,1)    0%,
    rgba(10,10,10,0.88) 28%,
    rgba(10,10,10,0.4)  52%,
    rgba(10,10,10,0.08) 72%,
    transparent         100%
  );
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
  background: linear-gradient(
    to top,
    rgba(22,22,22,1)    0%,
    rgba(22,22,22,0.9)  28%,
    rgba(22,22,22,0.45) 52%,
    transparent         75%
  );
}

.poster-overlay {
  position: absolute;
  bottom: 0; left: 0; right: 0;
  padding: 0.75rem 0.7rem 0.65rem;
  z-index: 1;
}

/* ── improved poster title typography ── */
.poster-title {
  font-size: 0.88rem;
  font-weight: 500;
  color: #f0ece5;
  letter-spacing: 0.15px;
  line-height: 1.25;
  margin-bottom: 0.35rem;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-shadow:
    0 1px 3px rgba(0,0,0,0.9),
    0 2px 8px rgba(0,0,0,0.7);
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
.tag-anime { background: rgba(126,184,200,0.15); color: var(--anime); border: 1px solid rgba(126,184,200,0.3); }
.tag-film  { background: rgba(200,126,154,0.15); color: var(--film);  border: 1px solid rgba(200,126,154,0.3); }
.tag-show  { background: rgba(154,200,126,0.15); color: var(--show);  border: 1px solid rgba(154,200,126,0.3); }

.entry-score {
  font-family: 'DM Mono', monospace;
  font-size: 0.65rem;
  color: var(--accent);
}

.entry-score::before {
  content: "★";
  margin-right: 4px;
  color: var(--accent);
  font-size: 0.95rem;
}

.status-dot {
  width: 10px;
  height: 10px;
  border-radius: 3px;
  flex-shrink: 0;
  position: relative;
  transition: transform 0.2s ease;
}

.status-dot::after {
  content: '';
  position: absolute;
  inset: -2px;
  border-radius: inherit;
  background: inherit;
  filter: blur(4px);
  opacity: 0.4;
  z-index: -1;
}

.dot-watching {
  background: #a78ee6;
  box-shadow: 0 0 10px rgba(167, 142, 230, 0.3);
  animation: pulse-dot 2s infinite;
}

.dot-finished {
  background: #7ec89a;
  box-shadow: 0 0 8px rgba(126, 200, 154, 0.2);
}

.dot-dropped {
  background: #c87e7e;
  opacity: 0.8;
}

.dot-planned {
  background: transparent;
  border: 1.5px solid var(--muted);
  box-sizing: border-box;
  opacity: 0.6;
}

@keyframes pulse-dot {
  0% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.1); opacity: 0.8; }
  100% { transform: scale(1); opacity: 1; }
}

.status-dot:hover {
  transform: scale(1.2);
}

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

/* ── infinite scroll loader ── */
.load-sentinel {
  height: 1px;
  margin-top: 2rem;
}

.load-spinner {
  display: none;
  justify-content: center;
  align-items: center;
  padding: 2rem 0;
  gap: 0.5rem;
  font-family: 'DM Mono', monospace;
  font-size: 0.7rem;
  color: var(--muted);
  letter-spacing: 0.06em;
}
.load-spinner.visible { display: flex; }

.spinner-dots {
  display: flex;
  gap: 4px;
}
.spinner-dots span {
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: var(--muted);
  animation: dot-bounce 1.2s infinite ease-in-out;
}
.spinner-dots span:nth-child(2) { animation-delay: 0.2s; }
.spinner-dots span:nth-child(3) { animation-delay: 0.4s; }

@keyframes dot-bounce {
  0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
  40% { transform: scale(1); opacity: 1; }
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
  font-size: 1.1rem;
  font-weight: 500;
  margin: 1.5rem 0 0.5rem;
  color: #e0dbd3;
}
.entry-body h4 {
  font-size: 0.95rem;
  font-weight: 500;
  margin: 1.25rem 0 0.4rem;
  color: var(--text);
}
.entry-body p {
  margin-bottom: 0.85rem;
  color: var(--text);
  font-size: 1.05rem;
}
.entry-body ul, .entry-body ol {
  padding-left: 1.4rem;
  margin-bottom: 0.85rem;
}
.entry-body li {
  color: var(--text);
  margin-bottom: 0.25rem;
  font-size: 1.05rem;
}
.entry-body ol { list-style-type: decimal; }
.entry-body code {
  font-family: 'DM Mono', monospace;
  font-size: 0.85em;
  background: #1f1f1f;
  padding: 0.1em 0.35em;
  border-radius: 2px;
  color: var(--accent);
}
.entry-body pre {
  background: #141414;
  border: 1px solid var(--border);
  border-radius: 4px;
  padding: 1rem 1.1rem;
  overflow-x: auto;
  margin-bottom: 1rem;
}
.entry-body pre code {
  background: none;
  padding: 0;
  font-size: 0.82rem;
  color: #c8c0b4;
  border-radius: 0;
}
.entry-body blockquote {
  border-left: 2px solid var(--accent);
  margin: 1.25rem 0;
  padding: 0.1rem 0 0.1rem 1.1rem;
}
.entry-body blockquote p {
  color: var(--muted);
  font-style: italic;
  margin-bottom: 0.3rem;
}
.entry-body .md-hr {
  border: none;
  border-top: 1px solid var(--border);
  margin: 1.75rem 0;
}
.entry-body a {
  color: var(--accent);
  text-decoration: underline;
  text-underline-offset: 3px;
  text-decoration-thickness: 1px;
  transition: opacity 0.15s;
}
.entry-body a:hover { opacity: 0.75; }
.entry-body del {
  color: var(--muted);
  text-decoration-color: var(--muted);
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

# Page size for infinite scroll
PAGE_SIZE = 24

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
  <div class="grid" id="grid">{cards}
  </div>
  <div class="load-spinner" id="spinner">
    <div class="spinner-dots"><span></span><span></span><span></span></div>
  </div>
  <div class="load-sentinel" id="sentinel"></div>
</div>
<script>
const btns        = document.querySelectorAll('.filter-btn');
const allCards    = Array.from(document.querySelectorAll('.poster-card'));
const searchInput = document.querySelector('.search-input');
const grid        = document.getElementById('grid');
const spinner     = document.getElementById('spinner');
const sentinel    = document.getElementById('sentinel');
const PAGE_SIZE   = {PAGE_SIZE};

let activeFilter  = 'all';
let visibleCards  = [];   // filtered set
let renderedCount = 0;    // how many are currently shown

/* ── hide all cards initially — JS controls visibility ── */
allCards.forEach(c => c.style.display = 'none');

function getFilteredCards() {{
  const raw    = searchInput.value.trim().toLowerCase();
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

  return allCards.filter(card => {{
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

    return filterOk && titleOk && scoreOk && yearOk && studioOk;
  }});
}}

function applyFilters() {{
  /* hide everything first */
  allCards.forEach(c => c.style.display = 'none');

  visibleCards  = getFilteredCards();
  renderedCount = 0;

  document.getElementById('count').textContent = visibleCards.length;
  renderNextPage();
}}

function renderNextPage() {{
  const batch = visibleCards.slice(renderedCount, renderedCount + PAGE_SIZE);
  batch.forEach(c => c.style.display = '');
  renderedCount += batch.length;

  /* hide spinner once all cards are shown */
  if (renderedCount >= visibleCards.length) {{
    spinner.classList.remove('visible');
  }}
}}

/* ── IntersectionObserver for infinite scroll ── */
const observer = new IntersectionObserver(entries => {{
  if (!entries[0].isIntersecting) return;
  if (renderedCount >= visibleCards.length) return;

  spinner.classList.add('visible');
  /* small delay so the spinner is perceptible */
  setTimeout(() => {{
    renderNextPage();
  }}, 280);
}}, {{ rootMargin: '200px' }});

observer.observe(sentinel);

/* ── filter buttons ── */
btns.forEach(btn => {{
  btn.addEventListener('click', () => {{
    btns.forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    activeFilter = btn.dataset.filter;
    applyFilters();
  }});
}});

/* ── search ── */
let searchTimer;
searchInput.addEventListener('input', () => {{
  clearTimeout(searchTimer);
  searchTimer = setTimeout(applyFilters, 120);
}});

/* ── initial render ── */
applyFilters();
</script>"""

with open(f'{OUT}/index.html', 'w', encoding='utf-8') as f:
    f.write(base_html('media-log', index_body))

print(f"✓ built {len(all_entries)} entries → {OUT}/")
