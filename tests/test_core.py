import struct
import unittest
import xml.etree.ElementTree as ET
from pattern_ferry.core import Clip,Note,Unsupported,midi_read,midi_write,xpt_read,xpt_write,vlq

class ExchangeTests(unittest.TestCase):
    def setUp(self):
        self.clip=Clip([Note(0,60,48,200),Note(0,64,48,100),Note(0,67,48,50),Note(96,60,24,75),Note(120,60,24,125),Note(192,69,48,150)],384)
    def midi(self,body,ppqn=48,fmt=0):
        return b'MThd'+struct.pack('>IHHH',6,fmt,1,ppqn)+b'MTrk'+struct.pack('>I',len(body))+body
    def read(self,data,**kw):
        return midi_read(data,accept_velocity_scaling=True,**kw)
    def xml(self,modify):
        root=ET.fromstring(xpt_write(self.clip))
        modify(root)
        return ET.tostring(root)
    def test_xpt_roundtrip_exact_note_data(self):
        parsed=xpt_read(xpt_write(self.clip))
        self.assertEqual(parsed.notes,sorted(self.clip.notes))
        self.assertEqual(parsed.length,384)
    def test_native_inert_doctype(self):
        data=xpt_write(self.clip).replace(b'<lmms-project',b'<!DOCTYPE lmms-project>\n<lmms-project',1)
        self.assertEqual(len(xpt_read(data).notes),6)
    def test_velocity_scaling_requires_acceptance_both_directions(self):
        with self.assertRaisesRegex(Unsupported,'Review required'):
            midi_write(self.clip)
        data,_=midi_write(self.clip,accept_velocity_scaling=True)
        with self.assertRaisesRegex(Unsupported,'Review required'):
            midi_read(data)
    def test_handwritten_roundtrip_loss_is_visible(self):
        data,report=midi_write(self.clip,accept_velocity_scaling=True)
        self.assertEqual([r['to'] for r in report if r['kind']=='velocity'],[127,64,32,48,79,95])
        result=self.read(data)
        self.assertEqual(result.notes,[Note(0,60,48,200),Note(0,64,48,101),Note(0,67,48,50),Note(96,60,24,76),Note(120,60,24,124),Note(192,69,48,150)])
        self.assertEqual(result.length,384)
    def test_adjacent_retrigger_serialized_off_before_on(self):
        c=Clip([Note(0,60,48,200),Note(48,60,48,100)],96)
        data,_=midi_write(c,accept_velocity_scaling=True)
        self.assertIn(b'\x30\x80\x3c\x00\x00\x90\x3c\x40',data)
        self.assertEqual(len(self.read(data).notes),2)
    def test_running_status(self):
        data=self.midi(b'\x00\x90\x3c\x64\x30\x3c\x00\x00\xff\x2f\x00')
        self.assertEqual(self.read(data).notes,[Note(0,60,48,157)])
    def test_quantization_needs_review_and_reports_errors(self):
        data=self.midi(b'\x01\x90\x3c\x64\x18\x80\x3c\x00\x00\xff\x2f\x00',ppqn=100)
        with self.assertRaisesRegex(Unsupported,'Nonintegral'):
            self.read(data)
        clip=self.read(data,quantize=True)
        q=[x for x in clip.review if x['kind']=='quantization'][0]
        self.assertEqual(q['start_error_ticks'],'-12/25')
        self.assertEqual(clip.notes,[Note(0,60,12,157)])
    def test_quantization_collapse_rejected(self):
        data=self.midi(b'\x00\x90\x3c\x64\x01\x80\x3c\x00\x00\xff\x2f\x00',ppqn=480)
        with self.assertRaises(Unsupported):
            self.read(data,quantize=True)
    def test_quantization_induced_overlap_rejected(self):
        c=Clip([Note(0,60,49,100),Note(48,60,10,100)],192)
        with self.assertRaisesRegex(Unsupported,'Same-pitch'):
            midi_write(c,accept_velocity_scaling=True)
    def test_xml_unsupported_scope(self):
        mutations={
            'step clip':lambda r:r[1].set('type','0'),
            'step note':lambda r:r[1][0].set('type','1'),
            'pan':lambda r:r[1][0].set('pan','1'),
            'detune':lambda r:ET.SubElement(r[1][0],'detuning'),
            'trim offset':lambda r:r[1].set('off','48'),
            'trim right':lambda r:r[1].set('len','100'),
            'muted':lambda r:r[1].set('muted','1'),
            'unknown root':lambda r:r.set('future','1'),
            'step context':lambda r:r[1].set('steps','abc'),
            'nondefault steps':lambda r:r[1].set('steps','32'),
            'invalid source position':lambda r:r[1].set('pos','abc'),
            'invalid color':lambda r:r[1].set('color','junk'),
            'unknown clip':lambda r:r[1].set('future','1'),
            'unknown note':lambda r:r[1][0].set('future','1'),
            'head metadata':lambda r:r[0].set('bpm','140'),
            'version':lambda r:r.set('version','30'),
            'negative position':lambda r:r[1][0].set('pos','-1'),
            'fractional position':lambda r:r[1][0].set('pos','0.5'),
            'silent note':lambda r:r[1][0].set('vol','0'),
            'out of range pitch':lambda r:r[1][0].set('key','128'),
            'extra clip':lambda r:ET.SubElement(r,'midiclip'),
            'unknown child':lambda r:ET.SubElement(r[1],'automation'),
        }
        for label,mutation in mutations.items():
            with self.subTest(label=label), self.assertRaises(Unsupported):
                xpt_read(self.xml(mutation))
    def test_external_and_internal_dtd_rejected(self):
        for prefix in [b'<!DOCTYPE lmms-project SYSTEM "file:///etc/passwd">',b'<!DOCTYPE lmms-project [<!ENTITY x "abc">]>']:
            with self.assertRaises(Unsupported):
                xpt_read(prefix+xpt_write(self.clip))
    def test_xml_compression_or_malformed(self):
        for data in [b'garbage',b'PK\x03\x04',b'<lmms-project>',b'x'*2_097_153]:
            with self.assertRaises(Unsupported):
                xpt_read(data)
    def test_midi_unsupported_and_corrupt(self):
        bodies={
            'controller':b'\x00\xb0\x40\x7f',
            'program':b'\x00\xc0\x01',
            'sysex':b'\x00\xf0\x00',
            'bend':b'\x00\xe0\x00\x40',
            'pressure':b'\x00\xd0\x40',
            'overlap':b'\x00\x90\x3c\x40\x01\x90\x3c\x40',
            'unmatched off':b'\x00\x80\x3c\x00',
            'zero len':b'\x00\x90\x3c\x40\x00\x80\x3c\x00',
            'unterminated':b'\x00\x90\x3c\x40',
            'no end':b'',
            'unknown meta':b'\x00\xff\x7f\x00',
            'tempo change':b'\x01\xff\x51\x03\x07\xa1\x20',
            'invalid data':b'\x00\x90\xff\x40',
            'overlong vlq':b'\x80\x80\x80\x80\x00',
            'missing status':b'\x00\x3c\x40',
            'two channels':b'\x00\x90\x3c\x40\x01\x91\x40\x40',
        }
        for name,body in bodies.items():
            with self.subTest(name=name), self.assertRaises(Unsupported):
                self.read(self.midi(body+b'\x00\xff\x2f\x00'))
    def test_smpte_and_async_rejected(self):
        for ppqn,fmt in [(0xe728,0),(0,0),(48,2)]:
            with self.assertRaises(Unsupported):
                self.read(self.midi(b'\x00\xff\x2f\x00',ppqn,fmt))
    def test_empty_zero_velocity_and_overlap_clips(self):
        for clip in [Clip([],192),Clip([Note(0,60,48,0)],192),Clip([Note(0,60,49,100),Note(48,60,1,100)],192)]:
            with self.assertRaises(Unsupported):
                midi_write(clip,accept_velocity_scaling=True)
    def test_utf16_entities_pi_and_text_rejected(self):
        xml=xpt_write(self.clip).decode('utf-8')
        xml=xml[xml.index('<lmms-project'):]
        malicious='<!DOCTYPE lmms-project [<!ENTITY v "100">]>'+xml.replace('vol="200"','vol="&v;"')
        variants=[malicious.encode('utf-16'),malicious.encode('utf-16-le'),('\x00'+xml).encode(),('<?alien unsupported?>'+xml).encode(),xml.replace('<head />','<head>unexpected</head>').encode(),xml.replace('key="60"','key="60"').replace('type="0" />','type="0">unexpected</note>',1).encode(),xml.replace('<head />','<head />unexpected').encode()]
        for data in variants:
            with self.subTest(data=data[:40]), self.assertRaises(Unsupported):
                xpt_read(data)
    def test_doctype_only_in_single_prolog_position(self):
        data=xpt_write(self.clip)
        for bad in [data.replace(b'key="60"',b'key="<!DOCTYPE lmms-project>60"',1),data.replace(b'<lmms-project',b'<!DOCTYPE lmms-project><!DOCTYPE lmms-project><lmms-project',1)]:
            with self.assertRaises(Unsupported):xpt_read(bad)
    def test_xml_nesting_and_element_caps(self):
        for data in [b'<a>'*9+b'</a>'*9,b'<a>'+b'<b/>'*4100+b'</a>']:
            with self.assertRaises(Unsupported):xpt_read(data)
    def test_midi_event_cap(self):
        body=b'\x00\xff\x01\x00'*16385+b'\x00\xff\x2f\x00'
        with self.assertRaisesRegex(Unsupported,'Too many MIDI events'):
            self.read(self.midi(body))
    def test_context_changes_reported(self):
        data=self.xml(lambda r:r[1].set('autoresize','1'))
        clip=xpt_read(data)
        self.assertEqual(clip.review[0]['source']['autoresize'],'1')
        self.assertEqual(clip.review[0]['return_defaults']['autoresize'],0)
    def test_vlq_boundaries(self):
        self.assertEqual(vlq(127),b'\x7f')
        self.assertEqual(vlq(128),b'\x81\x00')
        with self.assertRaises(Unsupported):vlq(1<<28)

if __name__=='__main__':
    unittest.main()
