"""Original test inputs, deliberately not claimed to be native-exported XPT."""
from pathlib import Path
import json
import xml.etree.ElementTree as ET

OUT=Path('evidence')
OUT.mkdir(exist_ok=True)
# Literal hand-written oracle: chord, rest, adjacent same-pitch retrigger,
# distinct velocities, then another rest and note. All values use 48 PPQN.
SOURCE=[(0,60,48,200),(0,64,48,100),(0,67,48,50),(96,60,24,75),(120,60,24,125),(192,69,48,150)]
EXPECTED_MIDI=[(0,60,48,127),(0,64,48,64),(0,67,48,32),(96,60,24,48),(120,60,24,79),(192,69,48,95)]
EXPECTED_IMPORTED=[(0,60,48,200),(0,64,48,101),(0,67,48,50),(96,60,24,76),(120,60,24,124),(192,69,48,150)]

def project(name,bpm,position,notes):
    root=ET.Element('lmms-project',version='31',type='song',creator='PatternFerry-fixture',creatorversion='1.3.0-alpha.2')
    ET.SubElement(root,'head',bpm=str(bpm),mastervol='100',masterpitch='0',timesig_numerator='4',timesig_denominator='4')
    song=ET.SubElement(root,'song')
    tc=ET.SubElement(song,'trackcontainer')
    track=ET.SubElement(tc,'track',type='0',name='Fixture instrument',muted='0',solo='0')
    instrument=ET.SubElement(track,'instrumenttrack',vol='47',pan='-11',pitch='3',basenote='57',usemasterpitch='1')
    ET.SubElement(ET.SubElement(instrument,'instrument',name='tripleoscillator'),'tripleoscillator',vol0='100',vol1='0',vol2='0')
    clip=ET.SubElement(track,'midiclip',type='1',name=name,autoresize='0',off='0',pos=str(position),muted='0',steps='16',len='384')
    for start,key,length,volume in notes:
        ET.SubElement(clip,'note',pos=str(start),key=str(key),len=str(length),vol=str(volume),pan='0',type='0')
    ET.indent(root)
    return ET.tostring(root,encoding='utf-8',xml_declaration=True)

(OUT/'source-input.mmp').write_bytes(project('SOURCE',120,0,SOURCE))
(OUT/'target-input.mmp').write_bytes(project('TARGET',137,192,[]))
(OUT/'oracle.json').write_text(json.dumps({'source_xpt':SOURCE,'midi':EXPECTED_MIDI,'imported_xpt':EXPECTED_IMPORTED,'clip_length':384,'destination_position':192,'destination_bpm':137},indent=2)+'\n')
