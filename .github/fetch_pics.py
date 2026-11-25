"""Download copies of the Heron Word Quest pictures from Wikimedia Commons.
Reads heron-word-quest/pics/manifest.txt and saves pics/<id>.jpg (960 px wide) and pics/t/<id>.jpg (330 px)."""
import io, os, sys, time, urllib.parse, urllib.request
from PIL import Image

ROOT = 'heron-word-quest/pics'
UA = 'HeronWordQuest/1.0 (https://budareezy07.github.io/heron-word-quest/; school reading app)'
SIZES = [(960, ''), (330, 't/')]

def fetch(name, width):
    url = 'https://commons.wikimedia.org/wiki/Special:FilePath/' + urllib.parse.quote(name) + f'?width={width}'
    for attempt in range(6):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': UA})
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read()
        except Exception as e:
            code = getattr(e, 'code', None)
            wait = 5 * (attempt + 1)
            print(f'  retry {attempt+1} for {name} @{width} ({code or e}); waiting {wait}s', flush=True)
            time.sleep(wait)
    return None

def save(data, path):
    im = Image.open(io.BytesIO(data))
    if im.mode in ('RGBA', 'LA', 'P'):
        im = im.convert('RGBA')
        bg = Image.new('RGB', im.size, (255, 255, 255))
        bg.paste(im, mask=im.split()[-1])
        im = bg
    else:
        im = im.convert('RGB')
    os.makedirs(os.path.dirname(path), exist_ok=True)
    im.save(path, 'JPEG', quality=86, optimize=True, progressive=True)

failed = []
for line in open(os.path.join(ROOT, 'manifest.txt'), encoding='utf-8'):
    line = line.rstrip('\n')
    if not line or line.startswith('#'):
        continue
    pid, name = line.split('\t', 1)
    for width, sub in SIZES:
        path = os.path.join(ROOT, sub + pid + '.jpg')
        if os.path.exists(path):
            continue
        data = fetch(name, width)
        if not data:
            failed.append(f'{pid}@{width}')
            continue
        try:
            save(data, path)
            print(f'saved {path} ({os.path.getsize(path)//1024} KB)', flush=True)
        except Exception as e:
            failed.append(f'{pid}@{width}: {e}')
        time.sleep(1)

print('FAILED:', failed if failed else 'none')
sys.exit(1 if failed else 0)
