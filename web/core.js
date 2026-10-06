/* Original dependency-free browser core. The Python prototype remains separate. */
(function (root) {
  'use strict';
  const LIMITS = Object.freeze({bytes: 2097152, notes: 4096, ticks: 10000000, events: 16384, tracks: 32, depth: 8});
  const PPQN = 48;
  function fail(code, detail) { const error = new Error(detail); error.code = code; throw error; }
  function need(ok, code, detail) { if (!ok) fail(code, detail); }
  function bytes(value) { need(value instanceof Uint8Array, 'INPUT', 'Expected file bytes'); need(value.byteLength <= LIMITS.bytes, 'SIZE', 'File exceeds 2 MiB'); return value; }
  function uint(text, label) { need(typeof text === 'string' && /^[0-9]{1,10}$/.test(text), 'NUMBER', `${label}: expected a bounded nonnegative integer`); return Number(text); }
  const gcd = (a,b) => b ? gcd(b,a % b) : Math.abs(a);
  function fraction(n,d=1) { need(Number.isSafeInteger(n) && Number.isSafeInteger(d) && d>0,'NUMBER','Invalid rational value'); const g=gcd(n,d)||1; return {n:n/g,d:d/g}; }
  function ftext(f) { return f.d===1 ? String(f.n) : `${f.n}/${f.d}`; }
  function nearest(n,d=1) { return Math.floor((2*n+d)/(2*d)); }
  const errtext = (target,n,d=1) => ftext(fraction(target*d-n,d));
  function keysOnly(attrs, allowed, kind) { for(const key of Object.keys(attrs)) need(allowed.includes(key),'FIELD',`Unsupported ${kind} field: ${key}`); }
  function validClip(clip, allowEmpty=false) {
    need(Number.isInteger(clip.length) && clip.length>0 && clip.length<=LIMITS.ticks,'BOUNDS','Clip length outside bounds');
    need(clip.notes.length >= (allowEmpty?0:1) && clip.notes.length<=LIMITS.notes,'NOTES','Expected 1–4096 regular notes');
    const ends=new Map();
    for(const n of [...clip.notes].sort((a,b)=>a.start-b.start || a.key-b.key)) {
      need([n.start,n.length,n.key,n.volume].every(Number.isInteger),'NUMBER','Note values must be integers');
      need(n.key>=0&&n.key<=127,'PITCH','Pitch outside MIDI range');
      need(n.volume>0&&n.volume<=200,'VELOCITY','Zero-volume or out-of-range note');
      need(n.start>=0&&n.length>0&&n.start+n.length<=clip.length,'TRIM','Trimmed or nonpositive-length note');
      need(n.start>=(ends.get(n.key)||0),'OVERLAP','Same-pitch overlap is unsupported');
      ends.set(n.key,n.start+n.length);
    }
    return clip;
  }
  // A deliberately small XML subset parser, independent of Python/ElementTree.
  // It accepts only element/attribute structure and whitespace, never resolves a DTD.
  function xmlTree(input) {
    let text;const data=bytes(input);
    try { text=new TextDecoder('utf-8',{fatal:true}).decode(data); }
    catch(error) { fail('ENCODING','Only UTF-8 XML is supported'); }
    need(!/[\u0000-\u0008\u000B\u000C\u000E-\u001F\uFFFE\uFFFF]/.test(text),'ENCODING','Invalid XML characters / UTF-16 are unsupported');
    text=text.replace(/^\uFEFF/,'').replace(/\r\n?/g,'\n');
    const declaration=/^<\?xml\s+version=(['"])1\.0\1(?:\s+encoding=(['"])(?:utf-8|UTF-8|utf8|UTF8)\2)?\s*\?>/;
    text=text.replace(declaration,'');
    text=text.replace(/^\s*<!DOCTYPE\s+lmms-project\s*>/,'');
    need(!/<!|<\?/.test(text),'XML_META','DTD subsets, entities, comments and processing instructions are unsupported');
    let p=0, count=0, rootNode=null;
    const stack=[];
    const white=()=>{while(p<text.length&&/[\t\n\r ]/.test(text[p]))p++;};
    const name=()=>{const m=/^[A-Za-z_][A-Za-z0-9_.:-]*/.exec(text.slice(p));need(m,'XML','Malformed XML name');p+=m[0].length;return m[0];};
    function entity(value) {
      need(!value.includes('<'),'XML','Raw markup in attribute');
      return value.replace(/&([^;]*);|&/g,(all,ref)=>{
        const named={amp:'&',lt:'<',gt:'>',quot:'"',apos:"'"};
        if(Object.hasOwn(named,ref))return named[ref];
        let cp;
        if(/^#[0-9]+$/.test(ref||''))cp=Number(ref.slice(1));
        else if(/^#x[0-9a-fA-F]+$/.test(ref||''))cp=parseInt(ref.slice(2),16);
        need(Number.isInteger(cp)&&(cp===9||cp===10||cp===13||(cp>=32&&cp<=0xD7FF)||(cp>=0xE000&&cp<=0xFFFD)||(cp>=0x10000&&cp<=0x10FFFF)),'XML_META','Unknown or invalid XML entity');
        return String.fromCodePoint(cp);
      });
    }
    while(p<text.length) {
      white(); if(p===text.length)break;
      need(text[p]==='<','XML_META','Non-whitespace XML text is unsupported');p++;
      if(text[p]==='/') { p++;const tag=name();white();need(text[p++]==='>'&&stack.length&&stack.at(-1).tag===tag,'XML','Mismatched close tag');stack.pop();continue; }
      const tag=name(), attrs=Object.create(null), node={tag,attrs,children:[]};
      count++;need(count<=LIMITS.notes+3,'XML_LIMIT','Too many XML elements');need(stack.length+1<=LIMITS.depth,'XML_LIMIT','XML nesting too deep');
      let selfClose=false;
      while(true) {
        const before=p;white();
        if(text[p]==='>'){p++;break;}
        if(text[p]==='/'&&text[p+1]==='>'){p+=2;selfClose=true;break;}
        need(p>before,'XML','Attributes must be separated by whitespace');
        const key=name();need(!Object.hasOwn(attrs,key),'XML','Duplicate XML attribute');white();need(text[p++]==='=','XML','Expected attribute equals');white();
        const quote=text[p++];need(quote==='"'||quote==="'",'XML','Expected quoted attribute');
        const end=text.indexOf(quote,p);need(end>=p,'XML','Unterminated attribute');attrs[key]=entity(text.slice(p,end).replace(/[\t\n]/g,' '));p=end+1;
        need(Object.keys(attrs).length<=12,'FIELD','Too many XML attributes');
      }
      if(stack.length)stack.at(-1).children.push(node);else {need(!rootNode,'XML','Multiple XML roots');rootNode=node;}
      if(!selfClose)stack.push(node);
    }
    need(rootNode&&stack.length===0,'XML','Unclosed or empty XML');return rootNode;
  }
  function parseXpt(input) {
    const rootNode=xmlTree(input), r=rootNode.attrs;
    need(rootNode.tag==='lmms-project'&&r.type==='midiclip','FORMAT','Expected a standalone midiclip XPT');
    need(r.version==='31','VERSION','Only experimental LMMS alpha.2 file version 31 is supported');
    keysOnly(r,['version','type','creator','creatorversion','creatorplatform','creatorplatformtype'],'root');
    need(rootNode.children.length===2&&rootNode.children[0].tag==='head'&&rootNode.children[1].tag==='midiclip','FORMAT','Expected head and one midiclip');
    const head=rootNode.children[0];need(!Object.keys(head.attrs).length&&!head.children.length,'FIELD','Head metadata is unsupported');
    const c=rootNode.children[1],a=c.attrs;
    keysOnly(a,['type','name','autoresize','off','color','pos','muted','steps','len'],'clip');
    need(a.type==='1','STEPS','Step/beat clips are unsupported');need((a.off??'0')==='0','TRIM','Trimmed clip offset is unsupported');
    need((a.muted??'0')==='0','MUTED','Muted clips are unsupported');need(['0','1'].includes(a.autoresize??'1'),'FIELD','Invalid autoresize');
    need((a.steps??'16')==='16','STEPS','Nondefault step editor context is unsupported');
    need(a.pos==='-1'||uint(a.pos??'0','clip position')<=LIMITS.ticks,'BOUNDS','Clip position outside bounds');
    need(a.color===undefined||/^#[a-fA-F0-9]{6}$/.test(a.color),'FIELD','Invalid clip color');need((a.name??'').length<=256,'FIELD','Clip name too long');
    const notes=c.children.map(n=>{
      need(n.tag==='note'&&!n.children.length,'DETUNE','Detune/automation or unknown children are unsupported');
      keysOnly(n.attrs,['key','vol','pan','len','pos','type'],'note');
      need((n.attrs.type??'0')==='0','STEPS','Step notes are unsupported');need((n.attrs.pan??'0')==='0','PAN','Per-note panning is unsupported');
      return {start:uint(n.attrs.pos,'note position'),key:uint(n.attrs.key,'pitch'),length:uint(n.attrs.len,'note length'),volume:uint(n.attrs.vol,'volume')};
    });
    const clip=validClip({notes,length:uint(a.len,'clip length'),name:a.name??'PatternFerry'});
    clip.context={name:a.name??'',color:a.color??null,pos:a.pos??'0',autoresize:a.autoresize??'1',steps:a.steps??'16'};return clip;
  }
  class Reader {
    constructor(data){this.data=data;this.p=0;}
    take(n){need(Number.isInteger(n)&&n>=0&&this.p+n<=this.data.length,'MIDI','Truncated MIDI');const out=this.data.slice(this.p,this.p+n);this.p+=n;return out;}
    byte(){return this.take(1)[0];}
    u16(){const b=this.take(2);return b[0]*256+b[1];}
    u32(){const b=this.take(4);return b[0]*16777216+b[1]*65536+b[2]*256+b[3];}
    text(n){return String.fromCharCode(...this.take(n));}
    vlq(){let n=0;for(let i=0;i<4;i++){const b=this.byte();n=n*128+(b&127);if(b<128)return n;}fail('MIDI','Overlong variable-length value');}
  }
  function parseMidi(input) {
    const r=new Reader(bytes(input));need(r.text(4)==='MThd'&&r.u32()===6,'MIDI','Invalid MIDI header');
    const format=r.u16(),tracks=r.u16(),ppqn=r.u16();
    need((format===0||format===1)&&tracks>=1&&tracks<=LIMITS.tracks&&(format!==0||tracks===1),'MIDI','Only MIDI format 0/1 with 1–32 tracks is supported');
    need(ppqn>0&&ppqn<32768,'SMPTE','SMPTE division is unsupported');
    const notes=[],meta=[],channels=new Set(),noteTracks=new Set();let endTick=0,eventCount=0;
    for(let i=0;i<tracks;i++) {
      need(r.text(4)==='MTrk','MIDI','Expected MIDI track');const t=new Reader(r.take(r.u32()));let tick=0,status=null,ended=false;const active=new Map();
      while(t.p<t.data.length) {
        need(++eventCount<=LIMITS.events,'MIDI_LIMIT','Too many MIDI events');tick+=t.vlq();need(tick<=Math.floor(LIMITS.ticks*ppqn/PPQN),'BOUNDS','MIDI duration outside bounds');
        let kind=t.byte();if(kind<128){need(status!==null,'MIDI','Running status has no status byte');t.p--;kind=status;}
        if(kind===255) {
          status=null;const type=t.byte(),value=t.take(t.vlq());
          if(type===47){need(value.length===0&&t.p===t.data.length,'MIDI','Malformed end-of-track');ended=true;break;}
          if(type===81){need(tick===0&&value.length===3&&(value[0]*65536+value[1]*256+value[2])>0,'TEMPO','Tempo maps are unsupported');meta.push({kind:'tempo',microsecondsPerBeat:value[0]*65536+value[1]*256+value[2]});}
          else if(type===1||type===3){need(tick===0,'META','Timed text is unsupported');meta.push({kind:'text',message:'Text/track name not transferred'});}
          else fail('META',`Unsupported MIDI metadata 0x${type.toString(16)}`);
          continue;
        }
        need(kind!==240&&kind!==247,'SYSEX','SysEx is unsupported');need(kind>=128&&kind<=159,'CONTROLLER','Controllers, programs, bend, pressure and system events are unsupported');
        status=kind;const key=t.byte(),velocity=t.byte();need(key<128&&velocity<128,'MIDI','Invalid MIDI data bytes');
        channels.add(kind&15);noteTracks.add(i);need(channels.size===1&&noteTracks.size===1,'CHANNEL','Only one note channel and one note track is supported');
        if((kind&240)===144&&velocity!==0){need(!active.has(key),'OVERLAP','Same-pitch overlapping note-ons are unsupported');active.set(key,{tick,velocity});}
        else {
          need(velocity===0,'RELEASE','Nonzero release velocity is unsupported');need(active.has(key),'MIDI','Unmatched note-off');const on=active.get(key);active.delete(key);need(tick>on.tick,'TRIM','Zero-length MIDI note');
          notes.push({start:on.tick,end:tick,key,velocity:on.velocity});need(notes.length<=LIMITS.notes,'NOTES','Too many notes');
        }
      }
      need(ended&&active.size===0,'MIDI','Missing end-of-track or unterminated notes');endTick=Math.max(endTick,tick);
    }
    need(r.p===r.data.length,'MIDI','Trailing bytes are unsupported');need(notes.length>0,'NOTES','Expected at least one note');
    return {notes,ppqn,length:endTick,meta,channels:[...channels]};
  }
  function reviewRow(key,sourceStart,sourceEnd,targetStart,targetEnd,sourceVelocity,targetVelocity,idealN,idealD) {
    return {key,sourceStart:ftext(sourceStart),sourceEnd:ftext(sourceEnd),targetStart,targetEnd,startError:errtext(targetStart,sourceStart.n,sourceStart.d),endError:errtext(targetEnd,sourceEnd.n,sourceEnd.d),sourceVelocity,targetVelocity,velocityIdeal:ftext(fraction(idealN,idealD)),velocityError:errtext(targetVelocity,idealN,idealD)};
  }
  function inspect(input,filename,{rounding='reject'}={}) {
    need(rounding==='reject'||rounding==='nearest','MODE','Invalid rounding policy');
    const lower=filename.toLowerCase();let plan;
    if(lower.endsWith('.xpt')) {
      const clip=parseXpt(input);
      const rows=clip.notes.map(n=>reviewRow(n.key,fraction(n.start),fraction(n.start+n.length),n.start,n.start+n.length,n.volume,nearest(n.volume*127,200),n.volume*127,200));
      plan={direction:'xpt-midi',clip,rows,inputPpqn:48,outputPpqn:48,requiresRounding:false,lengthExact:String(clip.length),lengthError:'0',context:clip.context,meta:[]};
    } else if(lower.endsWith('.mid')||lower.endsWith('.midi')) {
      const midi=parseMidi(input);let requiresRounding=false;
      const rows=midi.notes.map(n=>{const start=fraction(n.start*48,midi.ppqn),end=fraction(n.end*48,midi.ppqn);if(start.d!==1||end.d!==1)requiresRounding=true;return reviewRow(n.key,start,end,nearest(start.n,start.d),nearest(end.n,end.d),n.velocity,nearest(n.velocity*200,127),n.velocity*200,127);});
      const length=fraction(midi.length*48,midi.ppqn);if(length.d!==1)requiresRounding=true;
      const clip={notes:rows.map(n=>({start:n.targetStart,key:n.key,length:n.targetEnd-n.targetStart,volume:n.targetVelocity})),length:nearest(length.n,length.d),name:'PatternFerry'};
      plan={direction:'midi-xpt',clip,rows,inputPpqn:midi.ppqn,outputPpqn:48,requiresRounding,lengthExact:ftext(length),lengthError:errtext(clip.length,length.n,length.d),context:{channels:midi.channels},meta:midi.meta};
    } else fail('FORMAT','Choose .xpt, .mid or .midi; project files and compressed XPTZ are unsupported');
    plan.blocked=[];
    if(plan.requiresRounding&&rounding==='reject')plan.blocked.push({code:'ROUNDING',message:'Nonintegral 48-PPQN timing requires explicit nearest-tick selection and error review'});
    try{validClip(plan.clip);}catch(error){plan.blocked.push({code:error.code,message:error.message});}
    plan.rounding=rounding;plan.canExport=plan.blocked.length===0;plan.version='1.3.0-alpha.2';plan.audioEquivalence=false;
    return plan;
  }
  function vlq(value){need(Number.isInteger(value)&&value>=0&&value<268435456,'BOUNDS','MIDI delta outside bounds');const out=[value&127];while(value>=128){value=Math.floor(value/128);out.unshift((value&127)|128);}return out;}
  function writeMidi(clip){validClip(clip);const events=[];for(const n of clip.notes){const v=nearest(n.volume*127,200);need(v>0,'VELOCITY','Volume maps to a MIDI note-off');events.push({tick:n.start,priority:1,key:n.key,data:[144,n.key,v]},{tick:n.start+n.length,priority:0,key:n.key,data:[128,n.key,0]});}events.sort((a,b)=>a.tick-b.tick||a.priority-b.priority||a.key-b.key);const body=[0,255,81,3,7,161,32];let time=0;for(const event of events){body.push(...vlq(event.tick-time),...event.data);time=event.tick;}body.push(...vlq(clip.length-time),255,47,0);const n=body.length;return Uint8Array.from([77,84,104,100,0,0,0,6,0,0,0,1,0,48,77,84,114,107,(n>>>24)&255,(n>>>16)&255,(n>>>8)&255,n&255,...body]);}
  function writeXpt(clip){validClip(clip);const notes=[...clip.notes].sort((a,b)=>a.start-b.start||a.key-b.key);const lines=['<?xml version="1.0" encoding="utf-8"?>','<lmms-project version="31" type="midiclip" creator="PatternFerry" creatorversion="1.3.0-alpha.2">','  <head/>',`  <midiclip type="1" name="PatternFerry" autoresize="0" off="0" pos="0" muted="0" steps="16" len="${clip.length}">`,...notes.map(n=>`    <note key="${n.key}" vol="${n.volume}" pan="0" len="${n.length}" pos="${n.start}" type="0"/>`),'  </midiclip>','</lmms-project>',''];return new TextEncoder().encode(lines.join('\n'));}
  function exportPlan(plan,{acknowledged=false}={}){need(acknowledged,'ACK','Review acknowledgment is required');need(plan.canExport&&plan.blocked.length===0,'ROUNDING','Resolve blocked conversion before export');return plan.direction==='xpt-midi'?writeMidi(plan.clip):writeXpt(plan.clip);}
  const api=Object.freeze({LIMITS,PPQN,parseXpt,parseMidi,inspect,writeMidi,writeXpt,exportPlan,fraction,ftext,nearest});
  root.PatternFerryCore=api;if(typeof module!=='undefined'&&module.exports)module.exports=api;
})(globalThis);
