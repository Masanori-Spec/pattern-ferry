"""Verify and safely materialize the exact shipped source-only offline ZIP."""
from pathlib import Path
import hashlib,json,zipfile,stat
root=Path(__file__).resolve().parents[1]
manifest=json.loads((root/'offline-manifest.json').read_text())
archive=root/'pattern-ferry-offline.zip'
expected={'index.html','web/core.js','web/app.js','web/style.css','README-OFFLINE.txt'}
assert set(manifest['files'])==expected
assert hashlib.sha256(archive.read_bytes()).hexdigest()==manifest['zip_sha256']
output=root/'evidence/offline-app';output.mkdir(parents=True,exist_ok=True)
with zipfile.ZipFile(archive) as z:
    assert len(z.infolist())==len(expected) and set(z.namelist())==expected
    assert sum(info.file_size for info in z.infolist())<1048576
    for info in z.infolist():
        assert not stat.S_ISLNK(info.external_attr>>16)
        name=info.filename;data=z.read(name)
        assert hashlib.sha256(data).hexdigest()==manifest['files'][name]
        assert data==(root/name).read_bytes()
        target=output/name
        assert output.resolve() in target.resolve().parents
        target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
(root/'evidence/offline-package-result.json').write_text(json.dumps({'status':'pass','zip_sha256':manifest['zip_sha256'],'files':manifest['files'],'browser_app_root':'evidence/offline-app'},indent=2)+'\n')
print('Exact source-only offline ZIP verified and materialized for all browser/native tests')
