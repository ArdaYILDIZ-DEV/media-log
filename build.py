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

def format_date(d):
    try:
        return datetime.strptime(d, '%Y-%m-%d').strftime('%d %b %Y')
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
  max-width: 720px;
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
  max-width: 720px;
  margin: 0 auto;
  padding: 0 1.5rem 5rem;
}

/* ── index: cards ── */
.section-label {
  font-family: 'DM Mono', monospace;
  font-size: 0.7rem;
  color: var(--muted);
  letter-spacing: 0.12em;
  text-transform: uppercase;
  margin-bottom: 1.25rem;
}

.entries {
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.entry-card {
  background: var(--surface);
  border: 1px solid var(--border);
  padding: 1.1rem 1.25rem;
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 0.25rem 1rem;
  align-items: start;
  transition: border-color 0.15s, background 0.15s;
  cursor: pointer;
}
.entry-card:hover {
  border-color: var(--accent);
  background: #1a1a1a;
}
.entry-card:first-child { border-radius: 4px 4px 0 0; }
.entry-card:last-child  { border-radius: 0 0 4px 4px; }
.entry-card:only-child  { border-radius: 4px; }

.entry-title {
  font-size: 1.05rem;
  font-weight: 500;
  color: var(--text);
  line-height: 1.3;
}
.entry-meta {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  margin-top: 0.25rem;
}
.tag {
  font-family: 'DM Mono', monospace;
  font-size: 0.65rem;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  padding: 0.15rem 0.45rem;
  border-radius: 2px;
}
.tag-anime  { background: #7eb8c812; color: var(--anime);  border: 1px solid #7eb8c830; }
.tag-film   { background: #c87e9a12; color: var(--film);   border: 1px solid #c87e9a30; }
.tag-show   { background: #9ac87e12; color: var(--show);   border: 1px solid #9ac87e30; }

.entry-score {
  font-family: 'DM Mono', monospace;
  font-size: 0.75rem;
  color: var(--accent);
}
.entry-status {
  font-size: 0.8rem;
  color: var(--muted);
  font-style: italic;
}
.status-planned {
  font-family: 'DM Mono', monospace;
  font-size: 0.65rem;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  padding: 0.15rem 0.45rem;
  border-radius: 2px;
  background: #ffffff08;
  color: var(--muted);
  border: 1px dashed #3a3a3a;
  font-style: normal;
}
.entry-date {
  font-family: 'DM Mono', monospace;
  font-size: 0.7rem;
  color: var(--muted);
  text-align: right;
  white-space: nowrap;
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

/* ── responsive ── */
@media (max-width: 600px) {
  .entry-header h1 { font-size: 1.5rem; }
  .entry-card { grid-template-columns: 1fr; }
  .entry-date { text-align: left; }
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

# category dirs
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

        # attrs block
        attrs_html = ''
        for key in ['year', 'studio', 'score', 'status', 'date']:
            val = meta.get(key)
            if val:
                label = 'added' if key == 'date' else key
                display = format_date(val) if key == 'date' else val
                attrs_html += f'<span><span class="key">{label}</span><span class="val">{display}</span></span>\n'

        content = f"""
<div class="container">
  <a class="back-link" href="/media-log/index.html">← back</a>
  <div class="entry-header">
    <h1>{meta.get('title', s)}</h1>
    <div class="entry-attrs">
      <span><span class="key">type</span><span class="val"><span class="tag {tag_class}">{entry_type}</span></span></span>
      {attrs_html}
    </div>
  </div>
  <hr class="divider">
  <div class="entry-body">{md_to_html(body)}</div>
</div>"""

        page = base_html(meta.get('title', s), content)
        out_path = f'{OUT}/{cat}/{s}.html'
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(page)

        all_entries.append({
            'title': meta.get('title', s),
            'type': entry_type,
            'score': meta.get('score', ''),
            'status': meta.get('status', ''),
            'date': meta.get('date', ''),
            'date_fmt': format_date(meta.get('date', '')),
            'url': f'{cat}/{s}.html',
            'tag_class': tag_class,
        })

# sort by date descending
all_entries.sort(key=lambda e: e['date'], reverse=True)

# ── index page ───────────────────────────────────────────────────────────────

cards = ''
for e in all_entries:
    is_planned = e['status'].lower() == 'planned'
    score_html = '' if is_planned else (f'<span class="entry-score">{e["score"]}</span>' if e['score'] else '')
    if is_planned:
        status_html = '<span class="status-planned">planned</span>'
    elif e['status']:
        status_html = f'<span class="entry-status">{e["status"]}</span>'
    else:
        status_html = ''
    cards += f"""
<a href="{e['url']}" class="entry-card">
  <div>
    <div class="entry-title">{e['title']}</div>
    <div class="entry-meta">
      <span class="tag {e['tag_class']}">{e['type']}</span>
      {score_html}
      {status_html}
    </div>
  </div>
  <div class="entry-date">{e['date_fmt']}</div>
</a>"""

index_body = f"""
<div class="container">
  <div class="section-label">recent entries — {len(all_entries)} total</div>
  <div class="entries">{cards}
  </div>
</div>"""

with open(f'{OUT}/index.html', 'w', encoding='utf-8') as f:
    f.write(base_html('media-log', index_body))

print(f"✓ built {len(all_entries)} entries → {OUT}/")
