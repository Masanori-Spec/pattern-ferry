"""Strict, bounded interchange. No LMMS/Mido code or vendor binaries are bundled."""
from dataclasses import dataclass, field
from fractions import Fraction
import struct
import re
import xml.etree.ElementTree as ET

MAX_BYTES = 2 * 1024 * 1024
MAX_NOTES = 4096
MAX_TICKS = 10_000_000
MAX_MIDI_EVENTS = 16384
MAX_XML_ELEMENTS = MAX_NOTES + 3
MAX_XML_DEPTH = 8
PPQN = 48

class Unsupported(ValueError):
    pass

@dataclass(frozen=True, order=True)
class Note:
    start: int
    key: int
    length: int
    volume: int

@dataclass
class Clip:
    notes: list[Note]
    length: int
    name: str = 'PatternFerry'
    review: list[dict] = field(default_factory=list)


def require(ok, why):
    if not ok:
        raise Unsupported(why)


def integer(value, name):
    require(isinstance(value, str) and value.isascii() and value.isdecimal(), f'{name}: expected nonnegative integer')
    require(len(value) <= 10, f'{name}: value too large')
    return int(value)


def round_up_half(value):
    value = Fraction(value)
    return (2 * value.numerator + value.denominator) // (2 * value.denominator)


def validate(clip):
    require(type(clip.length) is int and 0 < clip.length <= MAX_TICKS, 'Clip length outside supported bounds')
    require(0 < len(clip.notes) <= MAX_NOTES, 'Expected 1..4096 regular notes')
    ends = {}
    for n in sorted(clip.notes):
        require(all(type(v) is int for v in (n.start,n.key,n.length,n.volume)), 'Note values must be integers')
        require(0 <= n.key <= 127, 'Pitch outside MIDI range')
        require(0 < n.volume <= 200, 'Zero-volume notes cannot be represented; volume must be 1..200')
        require(n.start >= 0 and n.length > 0 and n.start + n.length <= clip.length, 'Trimmed, negative, or nonpositive-length note')
        require(n.start >= ends.get(n.key, 0), 'Same-pitch overlap is ambiguous and unsupported')
        ends[n.key] = n.start + n.length
    return clip


def xpt_read(data):
    require(len(data) <= MAX_BYTES, 'XPT exceeds 2 MiB limit')
    try:
        text = data.decode('utf-8-sig')
    except UnicodeError as e:
        raise Unsupported('Only UTF-8 XML is supported') from e
    require('\x00' not in text, 'NUL/UTF-16 XML is unsupported')
    declared = re.search(r'<\?xml[^?]*encoding\s*=\s*[\"\']([^\"\']+)', text, re.I)
    require(declared is None or declared.group(1).lower() in ('utf-8','utf8'), 'Only UTF-8 XML is supported')
    require('<!ENTITY' not in text.upper(), 'Entities unsupported')
    # Qt emits this inert declaration. External/internal DTD subsets are rejected.
    text = re.sub(r'\A(\s*(?:<\?xml\b[^?]*\?>\s*)?)<!DOCTYPE\s+lmms-project\s*>', r'\1', text, count=1)
    require('<!DOCTYPE' not in text.upper(), 'External/internal DTD subsets unsupported')
    try:
        parser = ET.XMLPullParser(events=('start','end','pi','comment'))
        count, depth, root = 0, 0, None
        for offset in range(0,len(text),4096):
            parser.feed(text[offset:offset+4096])
            for event, element in parser.read_events():
                require(event not in ('pi','comment'), 'Processing instructions/comments unsupported')
                if event == 'start':
                    count += 1
                    depth += 1
                    require(count <= MAX_XML_ELEMENTS, 'Too many XML elements')
                    require(depth <= MAX_XML_DEPTH, 'XML nesting too deep')
                    if root is None:
                        root = element
                elif event == 'end':
                    require(not (element.text or '').strip() and not (element.tail or '').strip(), 'XML text metadata unsupported')
                    depth -= 1
        parser.close()
        require(root is not None, 'Empty XML')
        # Recheck after close: tails may arrive in a later parser chunk.
        for element in root.iter():
            require(not (element.text or '').strip() and not (element.tail or '').strip(), 'XML text metadata unsupported')
    except (ET.ParseError, ValueError) as e:
        if isinstance(e, Unsupported):
            raise
        raise Unsupported('Invalid XML/XPT; compressed XPTZ is unsupported') from e
    require(root.tag == 'lmms-project' and root.get('type') == 'midiclip', 'Expected standalone LMMS midiclip XPT')
    require(root.get('version') == '31', 'Only LMMS alpha.2 file version 31 supported')
    require(set(root.attrib) <= {'version', 'type', 'creator', 'creatorversion', 'creatorplatform', 'creatorplatformtype'}, 'Unsupported root fields')
    require(len(root) == 2 and root[0].tag == 'head' and root[1].tag == 'midiclip', 'Expected head and single midiclip')
    require(not root[0].attrib and not len(root[0]), 'Head metadata is unsupported')
    el = root[1]
    require(set(el.attrib) <= {'type','name','autoresize','off','color','pos','muted','steps','len'}, 'Unsupported clip fields')
    require(el.get('type') == '1', 'Step/beat clips unsupported')
    require(el.get('off','0') == '0', 'Trimmed clip offset unsupported')
    require(el.get('muted','0') == '0', 'Muted clips unsupported')
    require(el.get('autoresize','1') in ('0','1'), 'Invalid autoresize')
    require(el.get('steps','16') == '16', 'Only default 16-step editor context supported')
    require(el.get('pos','0') == '-1' or integer(el.get('pos','0'),'clip pos') <= MAX_TICKS, 'Clip position outside bounds')
    require(el.get('color') is None or re.fullmatch(r'#[0-9a-fA-F]{6}',el.get('color')), 'Invalid clip color')
    require(len(el.get('name','')) <= 256, 'Clip name too long')
    notes = []
    for n in el:
        require(n.tag == 'note' and not len(n), 'Detune/automation or unknown children unsupported')
        require(set(n.attrib) <= {'key','vol','pan','len','pos','type'}, 'Unsupported note fields')
        require(n.get('type','0') == '0', 'Step notes unsupported')
        require(n.get('pan','0') == '0', 'Per-note panning unsupported')
        notes.append(Note(integer(n.get('pos'), 'pos'), integer(n.get('key'), 'key'), integer(n.get('len'), 'len'), integer(n.get('vol'), 'vol')))
    clip = Clip(notes, integer(el.get('len'), 'clip len'), el.get('name','PatternFerry'))
    clip.review = [{'kind':'clip-context', 'source':{key:el.get(key,default) for key,default in [('name',''),('color',None),('pos','0'),('autoresize','1'),('steps','16')]}, 'return_defaults':{'name':'PatternFerry','color':None,'autoresize':0,'steps':16}, 'message':'Clip name/color/source position/editor behavior are not represented in MIDI. Return uses fixed length (autoresize=0) and default 16-step editor context; native import preserves destination position and instrument. Length is preserved as end-of-track time.'}]
    return validate(clip)


def xpt_write(clip):
    validate(clip)
    root = ET.Element('lmms-project', version='31', type='midiclip', creator='PatternFerry', creatorversion='1.3.0-alpha.2')
    ET.SubElement(root, 'head')
    el = ET.SubElement(root, 'midiclip', type='1', name=clip.name, autoresize='0', off='0', pos='0', muted='0', steps='16', len=str(clip.length))
    for n in sorted(clip.notes):
        ET.SubElement(el, 'note', key=str(n.key), vol=str(n.volume), pan='0', len=str(n.length), pos=str(n.start), type='0')
    ET.indent(root)
    return ET.tostring(root, encoding='utf-8', xml_declaration=True)


def vlq(value):
    require(0 <= value < (1 << 28), 'MIDI delta outside VLQ bounds')
    out = [value & 127]
    while value >> 7:
        value >>= 7
        out.insert(0, (value & 127) | 128)
    return bytes(out)


def midi_write(clip, *, accept_velocity_scaling=False):
    validate(clip)
    require(accept_velocity_scaling, 'Review required: volume 0..200 -> velocity 0..127 is lossy; explicitly accept velocity scaling')
    events = []
    changes = list(clip.review)
    for n in clip.notes:
        velocity = round_up_half(Fraction(n.volume * 127, 200))
        require(velocity > 0, 'Volume rounds to MIDI note-off; cannot export this note')
        changes.append({'kind':'velocity','key':n.key,'tick':n.start,'from':n.volume,'to':velocity})
        events += [(n.start, 1, n.key, bytes([0x90,n.key,velocity])), (n.start+n.length, 0, n.key, bytes([0x80,n.key,0]))]
    data = bytearray(b'\x00\xff\x51\x03\x07\xa1\x20')  # audition tempo 120 BPM, not imported into LMMS
    previous = 0
    for tick, _, _, message in sorted(events):
        data += vlq(tick-previous) + message
        previous = tick
    data += vlq(clip.length-previous) + b'\xff\x2f\x00'
    return b'MThd'+struct.pack('>IHHH',6,0,1,PPQN)+b'MTrk'+struct.pack('>I',len(data))+data, changes


class Reader:
    def __init__(self, data):
        self.data, self.pos = data, 0
    def take(self, count):
        require(count >= 0 and self.pos+count <= len(self.data), 'Truncated MIDI')
        out = self.data[self.pos:self.pos+count]
        self.pos += count
        return out
    def variable(self):
        value = 0
        for _ in range(4):
            b = self.take(1)[0]
            value = (value << 7) | (b & 127)
            if b < 128:
                return value
        raise Unsupported('Overlong MIDI VLQ')


def midi_read(data, *, accept_velocity_scaling=False, quantize=False):
    require(len(data) <= MAX_BYTES, 'MIDI exceeds 2 MiB limit')
    require(accept_velocity_scaling, 'Review required: velocity 1..127 -> volume 1..200 is a scale mapping; explicitly accept velocity scaling')
    r = Reader(data)
    require(r.take(4) == b'MThd', 'Not a MIDI file')
    require(struct.unpack('>I',r.take(4))[0] == 6, 'Unsupported MIDI header length')
    fmt, count, ppqn = struct.unpack('>HHH',r.take(6))
    require(fmt in (0,1) and 1 <= count <= 32, 'Only MIDI format 0/1, 1..32 tracks supported')
    require(fmt != 0 or count == 1, 'Format 0 must contain one track')
    require(0 < ppqn < 32768, 'SMPTE time division unsupported')
    notes, review, channels, note_tracks, total_end = [], [], set(), set(), 0
    event_count = 0
    for track in range(count):
        require(r.take(4) == b'MTrk', 'Expected MIDI track')
        t = Reader(r.take(struct.unpack('>I',r.take(4))[0]))
        tick, status, active, ended = 0, None, {}, False
        while t.pos < len(t.data):
            event_count += 1
            require(event_count <= MAX_MIDI_EVENTS, 'Too many MIDI events')
            tick += t.variable()
            require(tick <= MAX_TICKS * ppqn // PPQN, 'MIDI duration outside bounds')
            first = t.take(1)[0]
            if first < 128:
                require(status is not None, 'Running status without channel status')
                t.pos -= 1
                first = status
            if first == 0xFF:
                status = None
                kind = t.take(1)[0]
                payload = t.take(t.variable())
                if kind == 0x2F:
                    require(payload == b'' and t.pos == len(t.data), 'Malformed end-of-track')
                    ended = True
                    break
                if kind == 0x51:
                    require(tick == 0 and len(payload) == 3 and int.from_bytes(payload,'big') > 0, 'Tempo maps unsupported')
                    review.append({'kind':'tempo','microseconds_per_beat':int.from_bytes(payload,'big'),'message':'Audition metadata only; destination LMMS tempo is unchanged'})
                elif kind in (0x03,0x01):
                    require(tick == 0, 'Timed text metadata unsupported')
                    review.append({'kind':'text','message':'Track name/text not imported'})
                else:
                    raise Unsupported(f'Unsupported MIDI meta event 0x{kind:02x}')
                continue
            require(first not in (0xF0,0xF7), 'SysEx unsupported')
            require(0x80 <= first <= 0x9F, 'Controllers, program changes, pressure, bend and system events unsupported')
            status = first
            key, velocity = t.take(2)
            require(key < 128 and velocity < 128, 'Invalid MIDI data bytes')
            channel = first & 15
            channels.add(channel)
            note_tracks.add(track)
            require(len(channels) == 1 and len(note_tracks) == 1, 'Only one note channel and one note track supported')
            on = first & 0xF0 == 0x90 and velocity != 0
            if on:
                require(key not in active, 'Same-pitch overlapping note-ons unsupported')
                active[key] = (tick, velocity)
            else:
                require(velocity == 0, 'Nonzero release velocity unsupported')
                require(key in active, 'Unmatched note-off')
                start, vol = active.pop(key)
                require(tick > start, 'Zero-length MIDI note unsupported')
                start_l, end_l = Fraction(start * PPQN,ppqn), Fraction(tick * PPQN,ppqn)
                new_start, new_end = round_up_half(start_l), round_up_half(end_l)
                if start_l.denominator != 1 or end_l.denominator != 1:
                    require(quantize, 'Nonintegral 48-PPQN positions: review quantization errors and explicitly enable nearest-tick quantization')
                    review.append({'kind':'quantization','key':key,'start_exact':str(start_l),'end_exact':str(end_l),'start_error_ticks':str(Fraction(new_start)-start_l),'end_error_ticks':str(Fraction(new_end)-end_l)})
                mapped = round_up_half(Fraction(vol * 200,127))
                notes.append(Note(new_start,key,new_end-new_start,mapped))
                review.append({'kind':'velocity','key':key,'tick':new_start,'from':vol,'to':mapped})
                require(len(notes) <= MAX_NOTES, 'Too many notes')
        require(ended and not active, 'Missing end-of-track or unterminated notes')
        total_end = max(total_end,tick)
    require(r.pos == len(data), 'Trailing bytes unsupported')
    length_exact = Fraction(total_end*PPQN,ppqn)
    length = round_up_half(length_exact)
    if length_exact.denominator != 1:
        require(quantize, 'Nonintegral clip length requires quantization review')
        review.append({'kind':'quantization','clip_end_exact':str(length_exact),'end_error_ticks':str(Fraction(length)-length_exact)})
    review.append({'kind':'channel','source_channels':sorted(channels),'message':'MIDI channel/instrument context is not transferred; destination LMMS instrument is unchanged'})
    return validate(Clip(sorted(notes),length,review=review))
