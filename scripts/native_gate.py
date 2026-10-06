"""Operate an unmodified LMMS GUI through AT-SPI/X11, never by source injection.

Run only in hosted CI. Screenshots and accessibility trees remain on failure.
No helper writes a native-exported XPT or the native post-import project.
"""
import csv
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback
import pyatspi

ROOT=Path.cwd()
E=ROOT/'evidence'
STEPS=[]

def command(*args):
    return subprocess.check_output(args,text=True,stderr=subprocess.STDOUT)

def record(name):
    time.sleep(0.7)
    command('scrot',str(E/(name+'.png')))
    dump=[]
    for node in walk(pyatspi.Registry.getDesktop(0)):
        try:
            ext=node.queryComponent().getExtents(pyatspi.DESKTOP_COORDS)
            try:
                action=node.queryAction()
                actions=[action.getName(i) for i in range(action.nActions)]
            except Exception:
                actions=[]
            dump.append({'name':node.name,'description':node.description,'role':node.getRoleName(),'bounds':[ext.x,ext.y,ext.width,ext.height],'actions':actions})
        except Exception:
            pass
    (E/(name+'-accessibility.json')).write_text(json.dumps(dump,indent=2))
    STEPS.append(name)
    (E/'gui-steps.json').write_text(json.dumps(STEPS,indent=2))

def walk(root,depth=0):
    if depth>35:
        return
    yield root
    try:
        for i in range(root.childCount):
            yield from walk(root.getChildAtIndex(i),depth+1)
    except Exception:
        pass

def find(name,role=None,timeout=15):
    deadline=time.monotonic()+timeout
    while time.monotonic()<deadline:
        for n in walk(pyatspi.Registry.getDesktop(0)):
            try:
                if n.name==name and (role is None or n.getRoleName()==role):
                    if n.getState().contains(pyatspi.STATE_SHOWING):
                        return n
            except Exception:
                pass
        time.sleep(0.3)
    raise RuntimeError(f'Visible accessibility node not found: {name!r} / {role!r}')

def click_node(node):
    ext=node.queryComponent().getExtents(pyatspi.DESKTOP_COORDS)
    assert ext.width>0 and ext.height>0, 'Empty UI bounds'
    command('xdotool','mousemove',str(ext.x+ext.width//2),str(ext.y+ext.height//2),'click','1')
    time.sleep(.3)

def keys(*value):
    command('xdotool','key','--clearmodifiers',*value)
    time.sleep(.4)

def wait_file(name):
    p=E/name
    for _ in range(100):
        if p.exists() and p.stat().st_size>0:
            time.sleep(.5)
            return p
        time.sleep(.2)
    raise RuntimeError(f'Native application did not write {p}')

def filename(path):
    keys('alt+n','ctrl+a')
    command('xdotool','type','--clearmodifiers','--delay','1',str(path))
    keys('Return')

def active_project(path,timeout=15):
    deadline=time.monotonic()+timeout
    title='<no active window>'
    while time.monotonic()<deadline:
        try:
            title=command('xdotool','getactivewindow','getwindowname').strip()
        except subprocess.CalledProcessError:
            # The application/window manager may not yet own an active window.
            # Keep waiting within the same bounded deadline; never count as success.
            time.sleep(.2)
            continue
        if title.startswith((path.stem+' - LMMS 1.3.0-alpha.2',path.stem+'* - LMMS 1.3.0-alpha.2')):
            return title
        time.sleep(.2)
    raise RuntimeError(f'Expected active native project {path.stem!r}; actual title {title!r}')

def save_project_as(path):
    assert not path.exists(), f'Refusing stale native output: {path}'
    keys('ctrl+shift+s')
    filename(path)
    wait_file(path.name)
    active_project(path)

def open_project(path):
    keys('ctrl+o')
    deadline=time.monotonic()+15
    while time.monotonic()<deadline:
        title=command('xdotool','getactivewindow','getwindowname').strip()
        if title=='Project not saved':
            # Only original synthetic CI fixtures are open in this profile.
            # Save through the native warning instead of discarding changes.
            record('native-save-changes-warning')
            click_node(find('Save','push button'))
        elif title=='Open Project':
            break
        time.sleep(.2)
    wait_dialog('Open Project')
    find('Open',timeout=10)  # File dialog accept button
    filename(path)
    active_project(path)

def show_song_editor():
    # Ctrl+1 brings a background editor forward or hides the active one.
    # If it hid it, a second press restores it. This uses the official shortcut.
    keys('ctrl+1')
    try:
        editor=find('Song-Editor','frame',timeout=1)
    except RuntimeError:
        keys('ctrl+1')
        editor=find('Song-Editor','frame')
    ext=editor.queryComponent().getExtents(pyatspi.DESKTOP_COORDS)
    if ext.width<900:
        # R2 screenshot/AT-SPI identify the 24px native subwindow title bar.
        # Double-click that title to maximize, then verify the result.
        command('xdotool','mousemove',str(ext.x+ext.width//2),str(ext.y+12),'click','--repeat','2','--delay','120','1')
        time.sleep(.5)
        ext=find('Song-Editor','frame').queryComponent().getExtents(pyatspi.DESKTOP_COORDS)
    assert ext.width>=900, 'Song Editor did not maximize; clip lane remains hidden'
    record('visible-song-editor')
    return editor,ext

def clip(label):
    editor,editor_bounds=show_song_editor()
    matches=[]
    for n in walk(editor):
        try:
            if (n.name==label or n.description==label) and n.getState().contains(pyatspi.STATE_SHOWING):
                ext=n.queryComponent().getExtents(pyatspi.DESKTOP_COORDS)
                if ext.width>0 and ext.height>0 and ext.x>=editor_bounds.x and ext.x+ext.width<=editor_bounds.x+editor_bounds.width:
                    matches.append((n,ext))
        except Exception:
            pass
    if len(matches)==1:
        ext=matches[0][1]
        command('xdotool','mousemove',str(ext.x+ext.width//2),str(ext.y+ext.height//2),'click','--repeat','2','--delay','120','1')
        time.sleep(.7)
        return
    assert len(matches)==0, f'Ambiguous accessible clip label: {label}'
    # Native clip text is custom-painted and may have no AT-SPI node. OCR is
    # a read of the hosted screenshot; no coordinate is guessed silently.
    for attempt in range(5):
        shot=E/f'locate-{label}-{attempt}.png'
        command('scrot',str(shot))
        ocr=subprocess.run(['tesseract',str(shot),'stdout','--psm','11','tsv'],capture_output=True,text=True,check=True)
        result=ocr.stdout
        (E/f'locate-{label}-{attempt}-stderr.txt').write_text(ocr.stderr)
        (E/f'locate-{label}-{attempt}.tsv').write_text(result)
        hits=[row for row in csv.DictReader(io.StringIO(result),delimiter='\t') if (row.get('text') or '').strip().upper()==label]
        if len(hits)==1:
            h=hits[0]
            x=int(h['left'])+int(h['width'])//2
            y=int(h['top'])+int(h['height'])//2
            command('xdotool','mousemove',str(x),str(y),'click','--repeat','2','--delay','120','1')
            time.sleep(.7)
            return
        time.sleep(.5)
    raise RuntimeError(f'Cannot uniquely locate rendered {label} clip. Native gate stays unproven.')

def click_ocr_phrase(label,screenshot):
    result=subprocess.run(['tesseract',str(screenshot),'stdout','--psm','11','tsv'],capture_output=True,text=True,check=True)
    screenshot.with_suffix('.tsv').write_text(result.stdout)
    screenshot.with_suffix('.ocr-stderr.txt').write_text(result.stderr)
    lines={}
    for row in csv.DictReader(io.StringIO(result.stdout),delimiter='\t'):
        if row.get('level')!='5' or not (row.get('text') or '').strip():
            continue
        line=tuple(row.get(k) for k in ('page_num','block_num','par_num','line_num'))
        lines.setdefault(line,[]).append(row)
    target=label.lower().split()
    hits=[]
    for words in lines.values():
        for i in range(len(words)-len(target)+1):
            selected=words[i:i+len(target)]
            if [w['text'].strip().lower() for w in selected]==target:
                left=min(int(w['left']) for w in selected)
                top=min(int(w['top']) for w in selected)
                right=max(int(w['left'])+int(w['width']) for w in selected)
                bottom=max(int(w['top'])+int(w['height']) for w in selected)
                hits.append(((left+right)//2,(top+bottom)//2))
    assert len(hits)==1, f'Expected one visible OCR phrase {label!r}; found {len(hits)}'
    x,y=hits[0]
    command('xdotool','mousemove',str(x),str(y),'click','1')
    time.sleep(.3)

def wait_dialog(title,timeout=15):
    deadline=time.monotonic()+timeout
    while time.monotonic()<deadline:
        try:
            if command('xdotool','getactivewindow','getwindowname').strip()==title:
                return
        except subprocess.CalledProcessError:
            pass
        time.sleep(.2)
    raise RuntimeError(f'Expected native dialog {title!r}')

def file_action(action):
    toolbar=find('File actions')
    candidates=[]
    for n in walk(toolbar):
        try:
            if n.getRoleName() in ('push button','toggle button','menu button') and n.getState().contains(pyatspi.STATE_SHOWING):
                candidates.append(n)
        except Exception:
            pass
    assert len(candidates)==1, f'Expected one file menu button, found {len(candidates)}'
    click_node(candidates[0])
    stem='menu-'+action.lower().replace(' ','-')
    record(stem)
    try:
        item=find(action,timeout=2)
    except RuntimeError:
        # Qt's transient menu is visually present but absent from AT-SPI on
        # the pinned official build (recorded in R4). Click its unique OCR text.
        click_ocr_phrase(action,E/(stem+'.png'))
    else:
        click_node(item)
    wait_dialog('Export clip' if action=='Export clip' else 'Open clip')

try:
    for name in ['native-export.xpt','converted.mid','generated.xpt','source-native.mmp','target-before.mmp','target-after.mmp','target-reopened.mmp','native-gui-result.json','native-oracle-result.json']:
        assert not (E/name).exists(), f'Stale evidence exists: {name}'
    time.sleep(7)
    active_project(E/'source-input.mmp',timeout=60)
    record('01-native-start')
    clip('SOURCE')
    record('02-source-piano-roll')
    file_action('Export clip')
    record('03-export-dialog')
    filename(E/'native-export.xpt')
    wait_file('native-export.xpt')
    record('04-exported-source')
    # Opening/maximizing a clip can mark the source project modified. Save a
    # fresh native copy so switching projects cannot stop at an unsaved dialog.
    save_project_as(E/'source-native.mmp')
    # Python core is run separately; source is an actual native GUI output.
    command(sys.executable,'-m','pattern_ferry',str(E/'native-export.xpt'),str(E/'converted.mid'),'--report',str(E/'export-review.json'),'--accept-velocity-scaling')
    command(sys.executable,'-m','pattern_ferry',str(E/'converted.mid'),str(E/'generated.xpt'),'--report',str(E/'import-review.json'),'--accept-velocity-scaling')
    open_project(E/'target-input.mmp')
    record('05-target-existing-project')
    # Save a fresh native-normalized baseline, never reuse the input fixture.
    save_project_as(E/'target-before.mmp')
    clip('TARGET')
    record('06-target-empty-clip')
    file_action('Import clip')
    record('07-import-dialog')
    filename(E/'generated.xpt')
    time.sleep(1)
    record('08-imported-generated-xpt')
    save_project_as(E/'target-after.mmp')
    record('10-saved-native-project')
    # Load a different project first, so an ignored reopen cannot appear valid.
    open_project(E/'source-input.mmp')
    record('11-different-project-active')
    open_project(E/'target-after.mmp')
    record('12-reopened-after')
    save_project_as(E/'target-reopened.mmp')
    record('13-reopened-project-saved')
    (E/'native-gui-result.json').write_text(json.dumps({'status':'gui-complete-awaiting-independent-oracle','lmms':'1.3.0-alpha.2','route':'Piano Roll File actions > Export clip / Import clip','steps':STEPS},indent=2)+'\n')
except Exception:
    traceback.print_exc()
    try:
        record('FAILED-native-gate')
    except Exception:
        pass
    raise
