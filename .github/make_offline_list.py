"""Write heron-word-quest/offline.json: every picture, icon and sound the app can use offline, with a short content hash."""
import hashlib, json, os
ROOT = 'heron-word-quest'
files = {}
for folder, exts in [('pics', ('.jpg',)), ('pics/t', ('.jpg',)), ('emoji', ('.webp',)), ('sfx', ('.mp3',)), ('icons', ('.png',))]:
    d = os.path.join(ROOT, folder)
    if not os.path.isdir(d):
        continue
    for f in sorted(os.listdir(d)):
        p = os.path.join(d, f)
        if os.path.isfile(p) and f.endswith(exts):
            files[folder + '/' + f] = hashlib.sha1(open(p, 'rb').read()).hexdigest()[:10]
json.dump({'files': files}, open(os.path.join(ROOT, 'offline.json'), 'w'), separators=(',', ':'), sort_keys=True)
print(len(files), 'files listed')
