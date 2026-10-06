"""Package only original static sources; no browser/LMMS/SoundFont binaries."""
from pathlib import Path
import hashlib,json,zipfile
root=Path(__file__).resolve().parents[1]
files=['index.html','web/core.js','web/app.js','web/style.css','README-OFFLINE.txt']
with zipfile.ZipFile(root/'pattern-ferry-offline.zip','w',zipfile.ZIP_STORED) as z:
    for name in files:
        info=zipfile.ZipInfo(name,date_time=(2026,10,6,0,0,0))
        info.compress_type=zipfile.ZIP_STORED
        info.external_attr=0o644<<16
        z.writestr(info,(root/name).read_bytes())
manifest={name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in files}
(root/'offline-manifest.json').write_text(json.dumps({'files':manifest,'zip_sha256':hashlib.sha256((root/'pattern-ferry-offline.zip').read_bytes()).hexdigest()},indent=2)+'\n')
print(json.dumps(manifest,indent=2))
