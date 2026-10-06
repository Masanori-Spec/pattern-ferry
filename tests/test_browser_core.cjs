const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const C=require('../web/core.js');
const native=fs.readFileSync(path.join(__dirname,'../fixtures/native-alpha2-export.xpt'));
const encode=s=>new TextEncoder().encode(s);
const fixture=[{start:0,key:60,length:48,volume:200},{start:0,key:64,length:48,volume:100},{start:0,key:67,length:48,volume:50},{start:96,key:60,length:24,volume:75},{start:120,key:60,length:24,volume:125},{start:192,key:69,length:48,volume:150}];
function smf(body,ppqn=48,format=0){const n=body.length;return Uint8Array.from([77,84,104,100,0,0,0,6,0,format,0,1,ppqn>>8,ppqn&255,77,84,114,107,n>>>24,(n>>>16)&255,(n>>>8)&255,n&255,...body]);}
const eot=[0,255,47,0];
const code=(fn,expected)=>assert.throws(fn,e=>e.code===expected);
test('actual official alpha.2 export has six literal original notes',()=>{const c=C.parseXpt(native);assert.deepEqual(c.notes,fixture);assert.equal(c.length,384);});
test('handwritten velocity outputs and exact errors',()=>{const p=C.inspect(native,'native.xpt');assert.deepEqual(p.rows.map(r=>r.targetVelocity),[127,64,32,48,79,95]);assert.deepEqual(p.rows.map(r=>r.velocityError),['0','1/2','1/4','3/8','-3/8','-1/4']);assert.ok(p.rows.every(r=>r.startError==='0'&&r.endError==='0'));});
test('export acknowledgment required',()=>{const p=C.inspect(native,'n.xpt');code(()=>C.exportPlan(p),'ACK');assert.ok(C.exportPlan(p,{acknowledged:true}).length>20);});
test('MIDI bytes decode to literal tuples, EOT and reverse volumes',()=>{const p=C.inspect(native,'n.xpt'),mid=C.exportPlan(p,{acknowledged:true}),parsed=C.parseMidi(mid);assert.equal(parsed.ppqn,48);assert.equal(parsed.length,384);assert.deepEqual(parsed.notes.map(n=>[n.start,n.key,n.end-n.start,n.velocity]),[[0,60,48,127],[0,64,48,64],[0,67,48,32],[96,60,24,48],[120,60,24,79],[192,69,48,95]]);const back=C.inspect(mid,'n.mid');assert.deepEqual(back.clip.notes.map(n=>n.volume),[200,101,50,76,124,150]);assert.deepEqual(C.parseXpt(C.exportPlan(back,{acknowledged:true})).notes,back.clip.notes);});
test('MIDI roundtrip reference bytes are a fixed literal',()=>{const mid=C.writeMidi({notes:[{start:0,key:69,length:48,volume:200}],length:96});assert.equal(Buffer.from(mid).toString('hex'),'4d546864000000060000000100304d54726b0000001300ff510307a1200090457f3080450030ff2f00');});
test('same pitch off precedes adjacent on',()=>{const mid=C.writeMidi({notes:[{start:0,key:60,length:48,volume:200},{start:48,key:60,length:48,volume:100}],length:96});assert.ok(Buffer.from(mid).includes(Buffer.from([48,128,60,0,0,144,60,64])));assert.equal(C.parseMidi(mid).notes.length,2);});
test('fractional timing preview blocks default export and reports exact errors',()=>{const m=smf([1,144,60,100,24,128,60,0,...eot],100);const p=C.inspect(m,'n.mid');assert.equal(p.requiresRounding,true);assert.equal(p.canExport,false);assert.equal(p.rows[0].sourceStart,'12/25');assert.equal(p.rows[0].startError,'-12/25');code(()=>C.exportPlan(p,{acknowledged:true}),'ROUNDING');const q=C.inspect(m,'n.mid',{rounding:'nearest'});assert.equal(q.canExport,true);assert.equal(q.clip.notes[0].start,0);assert.equal(q.clip.notes[0].length,12);});
test('clip end quantization is explicit',()=>{const m=smf([0,144,60,100,24,128,60,0,1,255,47,0],100);const p=C.inspect(m,'n.mid',{rounding:'nearest'});assert.equal(p.lengthExact,'12');assert.equal(p.lengthError,'0');assert.equal(p.rows[0].endError,'12/25');});
test('collapsed rounded note remains blocked',()=>{const p=C.inspect(smf([0,144,60,100,1,128,60,0,47,255,47,0],480),'n.mid',{rounding:'nearest'});assert.equal(p.canExport,false);assert.ok(p.blocked.some(b=>b.code==='TRIM'));});
test('running status and zero-velocity note-off',()=>{const p=C.parseMidi(smf([0,144,60,100,48,60,0,...eot]));assert.deepEqual(p.notes,[{start:0,end:48,key:60,velocity:100}]);});
test('XML entity escaping is limited to characters and preserves literal name',()=>{let s=native.toString().replace('name="SOURCE"','name="A &amp; B &lt; &#x266A;"');assert.equal(C.parseXpt(encode(s)).name,'A & B < ♪');});
test('editor context values are retained for review',()=>{let s=native.toString().replace('autoresize="0"','autoresize="1"');const p=C.inspect(encode(s),'n.xpt');assert.equal(p.context.autoresize,'1');assert.equal(p.context.steps,'16');});
for(const [label,replace,expected]of [
 ['unknown root',s=>s.replace('version="31"','version="31" future="1"'),'FIELD'],
 ['unknown clip',s=>s.replace('off="0"','off="0" future="1"'),'FIELD'],
 ['unknown note',s=>s.replace('key="60"','key="60" future="1"'),'FIELD'],
 ['step clip',s=>s.replace(/<midiclip[^>]+>/,tag=>tag.replace('type="1"','type="0"')),'STEPS'],
 ['step note',s=>s.replace(/<note[^>]+>/,tag=>tag.replace('type="0"','type="1"')),'STEPS'],
 ['pan',s=>s.replace('pan="0"','pan="1"'),'PAN'],
 ['offset',s=>s.replace('off="0"','off="12"'),'TRIM'],
 ['short clip',s=>s.replace('len="384"','len="100"'),'TRIM'],
 ['muted',s=>s.replace('muted="0"','muted="1"'),'MUTED'],
 ['steps',s=>s.replace('steps="16"','steps="32"'),'STEPS'],
 ['bad auto',s=>s.replace('autoresize="0"','autoresize="2"'),'FIELD'],
 ['version',s=>s.replace('version="31"','version="30"'),'VERSION'],
 ['zero volume',s=>s.replace('vol="200"','vol="0"'),'VELOCITY'],
 ['pitch128',s=>s.replace('key="60"','key="128"'),'PITCH'],
 ['negative start',s=>s.replace('pos="96"','pos="-1"'),'NUMBER'],
 ['decimal start',s=>s.replace('pos="96"','pos="1.5"'),'NUMBER'],
 ['head text',s=>s.replace('<head/>','<head>bad</head>'),'XML_META'],
 ['tail text',s=>s.replace('<head/>','<head/>bad'),'XML_META'],
 ['comment',s=>s.replace('<head/>','<!-- bad --><head/>'),'XML_META'],
 ['PI',s=>s.replace('<head/>','<?bad bad?><head/>'),'XML_META'],
 ['attribute DTD',s=>s.replace('key="60"','key="<!DOCTYPE lmms-project>60"'),'XML_META'],
 ['second DTD',s=>s.replace('<!DOCTYPE lmms-project>','<!DOCTYPE lmms-project><!DOCTYPE lmms-project>'),'XML_META'],
 ['internal entity',s=>s.replace('<!DOCTYPE lmms-project>','<!DOCTYPE lmms-project [<!ENTITY x "x">]>'),'XML_META'],
 ['unknown entity',s=>s.replace('name="SOURCE"','name="&other;"'),'XML_META'],
 ['zero character entity',s=>s.replace('name="SOURCE"','name="&#0;"'),'XML_META'],
 ['duplicate attribute',s=>s.replace('key="60"','key="60" key="64"'),'XML'],
 ['invalid character',s=>s.replace('SOURCE','S\u0001OURCE'),'ENCODING']
])test(`reject XML ${label}`,()=>code(()=>C.parseXpt(encode(replace(native.toString()))),expected));
test('UTF16 entity bypass fails',()=>{const s=native.toString().replace('<!DOCTYPE lmms-project>','<!DOCTYPE lmms-project [<!ENTITY x "100">]>');code(()=>C.parseXpt(Buffer.from(s,'utf16le')),'ENCODING');});
test('nested XML bounded',()=>code(()=>C.parseXpt(encode('<x>'.repeat(9)+'</x>'.repeat(9))),'XML_LIMIT'));
test('element count bounded',()=>code(()=>C.parseXpt(encode('<x>'+'<y/>'.repeat(4100)+'</x>')),'XML_LIMIT'));
test('input size bounded before XML parsing',()=>code(()=>C.parseXpt(new Uint8Array(C.LIMITS.bytes+1)),'SIZE'));
for(const [label,body,expected]of [
 ['controller',[0,176,64,127],'CONTROLLER'],['program',[0,192,1],'CONTROLLER'],['bend',[0,224,0,64],'CONTROLLER'],['sysex',[0,240,0],'SYSEX'],['pressure',[0,208,64],'CONTROLLER'],['samepitch overlap',[0,144,60,64,1,144,60,64],'OVERLAP'],['unmatched off',[0,128,60,0],'MIDI'],['zero length',[0,144,60,64,0,128,60,0],'TRIM'],['unterminated',[0,144,60,64],'MIDI'],['unknown meta',[0,255,127,0],'META'],['tempo change',[1,255,81,3,7,161,32],'TEMPO'],['two channels',[0,144,60,64,1,145,64,64],'CHANNEL'],['nonzero release',[0,144,60,64,48,128,60,64],'RELEASE']
])test(`reject MIDI ${label}`,()=>code(()=>C.parseMidi(smf([...body,...eot])),expected));
test('SMPTE rejected',()=>code(()=>C.parseMidi(smf(eot,0xe728)),'SMPTE'));
test('asynchronous format2 rejected',()=>code(()=>C.parseMidi(smf(eot,48,2)),'MIDI'));
test('event count bounded',()=>{const body=[];for(let i=0;i<16385;i++)body.push(0,255,1,0);code(()=>C.parseMidi(smf([...body,...eot])),'MIDI_LIMIT');});
test('unknown extension rejected',()=>code(()=>C.inspect(native,'project.mmp'),'FORMAT'));

test('XML declaration must be at the document start',()=>{assert.throws(()=>C.parseXpt(encode(' \n'+native.toString())));});
test('literal XML attribute whitespace normalizes before character references',()=>{const source=native.toString().replace('name="SOURCE"','name="a\r\nb\tc&#9;d"');assert.equal(C.parseXpt(encode(source)).name,'a b c\td');});
