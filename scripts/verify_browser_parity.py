"""Use the original independent Python implementation to check real browser downloads."""
from pathlib import Path
import json
import sys
import xml.etree.ElementTree as ET
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pattern_ferry.core import xpt_read,midi_read,midi_write,xpt_write
E=Path('evidence')
source=xpt_read((E/'native-export.xpt').read_bytes())
python_mid,_=midi_write(source,accept_velocity_scaling=True)
assert python_mid==(E/'converted.mid').read_bytes(), 'Browser MIDI differs from independent Python output'
expected=midi_read((E/'converted.mid').read_bytes(),accept_velocity_scaling=True)
actual=xpt_read((E/'generated.xpt').read_bytes())
assert sorted(actual.notes)==sorted(expected.notes) and actual.length==expected.length
quant=midi_read((E/'quantization-input.mid').read_bytes(),accept_velocity_scaling=True,quantize=True)
actual_quant=xpt_read((E/'quantized.xpt').read_bytes())
assert sorted(actual_quant.notes)==sorted(quant.notes) and actual_quant.length==quant.length
result={'status':'pass','independent_python_comparison':True,'browser_midi_byte_exact':True,'browser_xpt_semantic_exact':True,'browser_quantized_xpt_semantic_exact':True}
(E/'browser-python-parity.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
