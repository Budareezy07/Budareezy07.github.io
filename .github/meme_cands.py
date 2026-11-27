"""Search Wikimedia Commons for free-licence photos to use as meme pictures. Saves 330 px thumbs and cands.json."""
import json, os, re, time, urllib.parse, urllib.request
UA = 'HeronWordQuest/1.0 (https://budareezy07.github.io/heron-word-quest/; school reading app)'
OUT = 'meme_cands'; os.makedirs(OUT + '/t', exist_ok=True)
QUERIES = [l.strip() for l in open('.github/meme_queries.txt', encoding='utf-8') if l.strip() and not l.startswith('#')]
OKLIC = re.compile(r'^(CC0|Public domain|PD|CC BY(-SA)? [0-9.]+( [a-z]{2})?)$', re.I)
def api(params):
    url = 'https://commons.wikimedia.org/w/api.php?' + urllib.parse.urlencode(params)
    for a in range(5):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': UA}), timeout=60) as r: return json.load(r)
        except Exception as e: print('retry', e, flush=True); time.sleep(5 * (a + 1))
    return {}
def strip(h): return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', h or '')).strip()
cands, seen = [], set()
for qi, q in enumerate(QUERIES):
    d = api({'action': 'query', 'format': 'json', 'generator': 'search', 'gsrnamespace': 6, 'gsrsearch': q + ' filetype:bitmap',
             'gsrlimit': 40, 'prop': 'imageinfo', 'iiprop': 'url|size|extmetadata|mime', 'iiurlwidth': 330})
    pages = sorted((d.get('query') or {}).get('pages', {}).values(), key=lambda p: p.get('index', 99))
    n = 0
    for p in pages:
        if n >= 10: break
        ii = (p.get('imageinfo') or [{}])[0]; em = ii.get('extmetadata') or {}
        lic = strip((em.get('LicenseShortName') or {}).get('value', ''))
        if not OKLIC.match(lic) or ii.get('mime') not in ('image/jpeg', 'image/png', 'image/webp'): continue
        if (ii.get('width') or 0) < 800 or (ii.get('height') or 0) < 500: continue
        t = p['title'][5:]
        if t in seen: continue
        seen.add(t); cid = f'q{qi:02d}_{n}'
        try:
            with urllib.request.urlopen(urllib.request.Request(ii['thumburl'], headers={'User-Agent': UA}), timeout=60) as r: open(f'{OUT}/t/{cid}.jpg', 'wb').write(r.read())
        except Exception as e: print('thumb fail', t, e); continue
        cands.append({'id': cid, 'q': q, 'file': t, 'lic': lic, 'artist': strip((em.get('Artist') or {}).get('value', '')),
                      'desc': strip((em.get('ImageDescription') or {}).get('value', ''))[:200], 'w': ii.get('width'), 'h': ii.get('height')})
        n += 1; time.sleep(0.3)
    print(q, n, flush=True)
json.dump(cands, open(OUT + '/cands.json', 'w'), indent=1)
print('total', len(cands))
