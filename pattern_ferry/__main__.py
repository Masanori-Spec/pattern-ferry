import argparse
import json
from pathlib import Path
from .core import MAX_BYTES, xpt_read, xpt_write, midi_read, midi_write, Unsupported

p=argparse.ArgumentParser(description='Experimental LMMS alpha.2 note-only XPT exchange. Review JSON is mandatory.')
p.add_argument('input',type=Path)
p.add_argument('output',type=Path)
p.add_argument('--report',type=Path,required=True)
p.add_argument('--accept-velocity-scaling',action='store_true')
p.add_argument('--preview',action='store_true',help='Write only proposed changes/errors; do not create the output')
p.add_argument('--quantize-nearest-tick',action='store_true')
a=p.parse_args()
try:
    resolved=[path.resolve() for path in (a.input,a.output,a.report)]
    if len(set(resolved))!=3:
        raise Unsupported('Input, output and report must be distinct paths')
    if a.output.exists() or a.report.exists():
        raise Unsupported('Refusing to overwrite an existing output or report')
    with a.input.open('rb') as source:
        data=source.read(MAX_BYTES+1)
    if len(data)>MAX_BYTES:
        raise Unsupported('Input exceeds 2 MiB limit')
    if a.input.suffix.lower()=='.xpt' and a.output.suffix.lower()=='.mid':
        output,review=midi_write(xpt_read(data),accept_velocity_scaling=(a.accept_velocity_scaling or a.preview))
    elif a.input.suffix.lower() in ('.mid','.midi') and a.output.suffix.lower()=='.xpt':
        clip=midi_read(data,accept_velocity_scaling=(a.accept_velocity_scaling or a.preview),quantize=(a.quantize_nearest_tick or a.preview))
        output,review=xpt_write(clip),clip.review
    else:
        raise Unsupported('Use .xpt -> .mid or .mid/.midi -> .xpt')
    # Exclusive creates preserve existing files even if a path appears after checks.
    with a.report.open('x',encoding='utf-8') as report:
        json.dump({'experimental':'LMMS 1.3.0-alpha.2','preview_only':a.preview,'audio_equivalence':False,'review':review},report,indent=2)
        report.write('\n')
    if not a.preview:
        with a.output.open('xb') as destination:
            destination.write(output)
except (Unsupported,OSError,RuntimeError) as e:
    p.exit(2,str(e)+'\n')
