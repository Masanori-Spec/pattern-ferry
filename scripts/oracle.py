"""Independent verifier: Mido plus direct XML, no converter imports."""
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import mido

E=Path('evidence')
expected=json.loads((E/'oracle.json').read_text())

def notes(element):
    return sorted([[int(n.get('pos')),int(n.get('key')),int(n.get('len')),int(n.get('vol'))] for n in element.findall('note')])

source=ET.parse(E/'native-export.xpt').getroot()
assert source.get('creator')=='LMMS', 'Export must be made by official app'
assert source.get('version')=='31' and source.get('type')=='midiclip'
assert notes(source.find('midiclip'))==sorted(expected['source_xpt'])
assert int(source.find('midiclip').get('len'))==expected['clip_length']

midi=mido.MidiFile(E/'converted.mid')
assert midi.type==0 and midi.ticks_per_beat==48 and len(midi.tracks)==1
active={}
seen=[]
tick=0
for msg in midi.tracks[0]:
    tick+=msg.time
    if msg.type=='note_on' and msg.velocity:
        assert msg.note not in active
        active[msg.note]=(tick,msg.velocity)
    elif msg.type in ('note_on','note_off'):
        start,velocity=active.pop(msg.note)
        seen.append([start,msg.note,tick-start,velocity])
assert not active and tick==expected['clip_length']
assert sorted(seen)==sorted(expected['midi'])

before=ET.parse(E/'target-before.mmp').getroot()
after=ET.parse(E/'target-after.mmp').getroot()
assert before.get('creator')==after.get('creator')=='LMMS', 'Both project files must have been saved natively'
bt=before.find('./song/trackcontainer/track')
at=after.find('./song/trackcontainer/track')
assert len(before.findall('./song/trackcontainer/track'))==1
assert len(after.findall('./song/trackcontainer/track'))==1
assert not notes(bt.find('midiclip')), 'The destination was an empty existing instrument clip'
assert notes(at.find('midiclip'))==sorted(expected['imported_xpt'])
assert int(at.find('midiclip').get('pos'))==expected['destination_position']
assert int(at.find('midiclip').get('len'))==expected['clip_length']
assert before.find('head').get('bpm')==after.find('head').get('bpm')==str(expected['destination_bpm'])

def canonical(el):
    return (el.tag, sorted(el.attrib.items()), el.text or '', el.tail or '', [canonical(c) for c in el])
assert canonical(bt.find('instrumenttrack'))==canonical(at.find('instrumenttrack')), 'Instrument state changed'
assert bt.attrib==at.attrib, 'Destination track settings changed'

reopened=ET.parse(E/'target-reopened.mmp').getroot()
assert reopened.get('creator')=='LMMS'
rt=reopened.find('./song/trackcontainer/track')
assert len(reopened.findall('./song/trackcontainer/track'))==1
assert notes(rt.find('midiclip'))==sorted(expected['imported_xpt'])
assert canonical(rt)==canonical(at), 'Native reopen changed destination track/clip/instrument'
assert canonical(reopened.find('head'))==canonical(after.find('head')), 'Native reopen changed project header'

# Strong negative controls prove the same assertions detect missing/shifted notes.
from copy import deepcopy
bad=deepcopy(at.find('midiclip'))
bad.remove(bad.findall('note')[0])
assert notes(bad)!=sorted(expected['imported_xpt'])
bad=deepcopy(at.find('midiclip'))
bad.findall('note')[0].set('pos','1')
assert notes(bad)!=sorted(expected['imported_xpt'])
result={'status':'pass','lmms':'1.3.0-alpha.2','native_export_import':True,'mido_handwritten_oracle':True,'preserved':['destination tempo','entire instrument state','track settings','destination clip timeline position'],'negative_controls':['missing note','shifted note'],'audio_equivalence':False,'files':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [E/'native-export.xpt',E/'converted.mid',E/'generated.xpt',E/'target-before.mmp',E/'target-after.mmp',E/'target-reopened.mmp']}}
(E/'native-oracle-result.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
