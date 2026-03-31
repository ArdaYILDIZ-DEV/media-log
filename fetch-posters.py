import os
import re
import urllib.request
import urllib.parse
import json

# ── config ────────────────────────────────────────────────────────────────────

try:
    with open('.tmdb_key') as f:
        API_KEY = f.read().strip()
except FileNotFoundError:
    print("HATA: .tmdb_key dosyası bulunamadı.")
    exit(1)

CATEGORIES = {
    'animes': 'tv',
    'shows':  'tv',
    'films':  'movie',
}

# ── helpers ───────────────────────────────────────────────────────────────────

def parse_frontmatter(text):
    meta = {}
    body = text
    m = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)', text, re.DOTALL)
    if m:
        for line in m.group(1).splitlines():
            if ':' in line:
                k, _, v = line.partition(':')
                meta[k.strip()] = v.strip()
        body = m.group(2)
    return meta, body, m.group(1) if m else ''

def tmdb_search(title, media_type, year=None):
    query = urllib.parse.quote(title)
    year_param = f"&year={year}" if year and media_type == 'movie' else (f"&first_air_date_year={year}" if year else "")
    url = f"https://api.themoviedb.org/3/search/{media_type}?api_key={API_KEY}&query={query}&language=en-US&page=1{year_param}"
    try:
        with urllib.request.urlopen(url, timeout=10) as r:
            data = json.loads(r.read())
        results = data.get('results', [])
        if not results:
            if year:
                return tmdb_search(title, media_type, year=None)
            return None
        poster = results[0].get('poster_path')
        if poster:
            return f"https://image.tmdb.org/t/p/w500{poster}"
    except Exception as e:
        print(f"  TMDB hata: {e}")
    return None

def inject_poster(filepath, poster_url):
    with open(filepath, encoding='utf-8') as f:
        raw = f.read()
    meta, body, fm_raw = parse_frontmatter(raw)

    if 'poster:' in fm_raw:
        # replace existing empty poster line
        new_fm = re.sub(r'poster:\s*$', f'poster: {poster_url}', fm_raw, flags=re.MULTILINE)
    else:
        # add after title line
        new_fm = re.sub(r'(title:.*)', r'\1\nposter: ' + poster_url, fm_raw, count=1)

    new_raw = f"---\n{new_fm}\n---\n{body}"
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_raw)

# ── main ──────────────────────────────────────────────────────────────────────

total = 0
updated = 0

for folder, media_type in CATEGORIES.items():
    if not os.path.isdir(folder):
        continue
    for fname in sorted(os.listdir(folder)):
        if not fname.endswith('.md'):
            continue
        filepath = f'{folder}/{fname}'
        with open(filepath, encoding='utf-8') as f:
            raw = f.read()
        meta, _, _ = parse_frontmatter(raw)
        title = meta.get('title', '')
        poster = meta.get('poster', '')

        total += 1

        if poster:
            print(f"  skip  {title} (poster zaten var)")
            continue

        if not title:
            print(f"  skip  {fname} (title yok)")
            continue

        year = meta.get('year', None)
        print(f"  search   {title} ({media_type}, {year or '?'})...", end=' ', flush=True)
        url = tmdb_search(title, media_type, year=year)
        if url:
            inject_poster(filepath, url)
            print(f"✓")
            updated += 1
        else:
            print(f"bulunamadı")

print(f"\n{updated}/{total} dosya güncellendi.")
