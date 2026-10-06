from pathlib import Path
import json
import subprocess
import sys
import tempfile
import unittest
from pattern_ferry.core import Clip,Note,xpt_write

class CliTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.directory=Path(self.temp.name)
        self.source=self.directory/'source.xpt'
        self.source.write_bytes(xpt_write(Clip([Note(0,69,48,100)],192)))
    def tearDown(self):self.temp.cleanup()
    def run_cli(self,output,report,*args):
        return subprocess.run([sys.executable,'-m','pattern_ferry',str(self.source),str(output),'--report',str(report),*args],capture_output=True,text=True)
    def test_alias_paths_rejected(self):
        output=self.directory/'out.mid'
        result=self.run_cli(output,self.directory/'sub'/'..'/'out.mid','--accept-velocity-scaling')
        self.assertNotEqual(result.returncode,0)
        self.assertIn('distinct',result.stderr)
        self.assertFalse(output.exists())
    def test_preview_writes_only_report(self):
        output=self.directory/'out.mid';report=self.directory/'review.json'
        result=self.run_cli(output,report,'--preview')
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertFalse(output.exists())
        self.assertTrue(json.loads(report.read_text())['preview_only'])
    def test_existing_files_not_overwritten(self):
        output=self.directory/'out.mid';output.write_bytes(b'keep')
        result=self.run_cli(output,self.directory/'review.json','--accept-velocity-scaling')
        self.assertNotEqual(result.returncode,0)
        self.assertEqual(output.read_bytes(),b'keep')
    def test_oversized_input(self):
        self.source.write_bytes(b'x'*2_097_153)
        result=self.run_cli(self.directory/'out.mid',self.directory/'review.json','--preview')
        self.assertNotEqual(result.returncode,0)
        self.assertIn('2 MiB',result.stderr)
