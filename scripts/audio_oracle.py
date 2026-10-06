"""Rendered-MIDI checks using official distro FluidSynth + TimGM, no audio-equivalence claim."""
from pathlib import Path
import json
import subprocess
import wave
import numpy as np
from pattern_ferry.core import Clip,Note,midi_write

E=Path('evidence')
SF=Path('/usr/share/sounds/sf2/TimGM6mb.sf2')
assert SF.is_file(), 'Official distro TimGM6mb SoundFont missing'
RESULT={'engine':subprocess.check_output(['fluidsynth','--version'],text=True).splitlines()[0], 'scope':'MIDI rendering only; not LMMS audio equivalence','soundfont':str(SF),'cases':{}}

def render(name,notes):
    midi,_=midi_write(Clip(notes,288),accept_velocity_scaling=True)
    (E/f'{name}.mid').write_bytes(midi)
    subprocess.run(['fluidsynth','-ni','-g','0.8','-R','0','-C','0','-r','22050','-F',str(E/f'{name}.wav'),str(SF),str(E/f'{name}.mid')],check=True)
    with wave.open(str(E/f'{name}.wav')) as w:
        assert w.getsampwidth()==2
        sr=w.getframerate()
        samples=np.frombuffer(w.readframes(w.getnframes()),dtype='<i2').reshape(-1,w.getnchannels()).mean(axis=1)/32768
    return sr,samples

def inspect(sr,samples):
    # Independent 5 ms RMS envelope, expected attacks one second apart.
    frame=round(sr*.005)
    rms=np.sqrt(np.mean(samples[:len(samples)//frame*frame].reshape(-1,frame)**2,axis=1))
    rising=[]
    threshold=float(max(rms)*.06)
    for i in range(len(rms)):
        if rms[i]>threshold and (i==0 or rms[i-1]<=threshold):
            when=i*frame/sr
            if not rising or when-rising[-1]>.15:
                rising.append(when)
    # Timbre may sustain, so attack evidence includes expected onset-local energy
    # plus a preceding silence region and a matched spectral fundamental.
    details=[]
    for onset,key in [(0,69),(1,72),(2,76)]:
        start=int((onset+.035)*sr)
        end=int((onset+.19)*sr)
        block=samples[start:end]
        assert len(block)>100
        energy=float(np.sqrt(np.mean(block**2)))
        assert energy>0.0004, f'Missing note near {onset}s'
        if onset:
            pre=samples[int((onset-.10)*sr):int((onset-.025)*sr)]
            assert float(np.sqrt(np.mean(pre**2)))<energy*.30, 'Onset preceded by excess energy'
        spectrum=np.abs(np.fft.rfft(block*np.hanning(len(block)),n=32768))
        freq=np.fft.rfftfreq(32768,1/sr)
        f0=440*2**((key-69)/12)
        window=(freq>f0*.965)&(freq<f0*1.035)
        peak_freq=float(freq[window][np.argmax(spectrum[window])])
        strongest=float(spectrum[(freq>100)&(freq<2000)].max())
        ratio=float(spectrum[window].max()/strongest)
        assert ratio>.20, f'Expected pitch {key} missing (ratio {ratio})'
        assert abs(peak_freq-f0)/f0<.02, f'Pitch mismatch for {key}'
        attacks=[x for x in rising if abs(x-onset)<.03]
        assert attacks, f'Expected onset absent at {onset}s; observed {rising}'
        details.append({'expected_key':key,'expected_onset_seconds':onset,'measured_onset_seconds':attacks[0],'fundamental_peak_hz':peak_freq,'fundamental_ratio':ratio})
    assert len(rising)==3, f'Unexpected attack count: {rising}'
    intervals=[rising[i+1]-rising[i] for i in range(2)]
    assert all(abs(x-1)<.03 for x in intervals), f'Onset interval mismatch {intervals}'
    return {'notes':details,'onset_intervals_seconds':intervals}

cases={'positive':[Note(0,69,24,160),Note(96,72,24,160),Note(192,76,24,160)],'missing-note':[Note(0,69,24,160),Note(192,76,24,160)],'shifted-note':[Note(0,69,24,160),Note(120,72,24,160),Note(192,76,24,160)]}
for name,notes in cases.items():
    sr,samples=render(name,notes)
    try:
        details=inspect(sr,samples)
    except AssertionError as exc:
        if name=='positive':
            raise
        RESULT['cases'][name]={'expected':'fail','actual':'fail','reason':str(exc)}
    else:
        assert name=='positive', f'Negative control unexpectedly passed: {name}'
        RESULT['cases'][name]={'expected':'pass','actual':'pass',**details}
RESULT['status']='pass'
(E/'audio-oracle-result.json').write_text(json.dumps(RESULT,indent=2)+'\n')
print(json.dumps(RESULT,indent=2))
