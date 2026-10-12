"""A two-cycle workload must gate on the same final-idle metric as the report."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'fragbench'))
from headroom import idle
class Headroom(unittest.TestCase):
 def test_final_idle_not_peak_or_average(self):
  row={'phases':[{'phase':'idle','cycle':1,'rss_bytes':100},
                 {'phase':'peak','cycle':1,'rss_bytes':1000},
                 {'phase':'idle','cycle':0,'rss_bytes':400}]}
  self.assertEqual(idle(row),100)
 def test_phase_average_cannot_authorize_model(self):
  base={'phases':[{'phase':'idle','cycle':0,'rss_bytes':400},{'phase':'idle','cycle':1,'rss_bytes':100}]}
  candidate={'phases':[{'phase':'idle','cycle':0,'rss_bytes':100},{'phase':'idle','cycle':1,'rss_bytes':99}]}
  self.assertFalse(idle(candidate)<idle(base)*.95)
 def test_single_idle(self):
  self.assertEqual(idle({'phases':[{'phase':'idle','rss_bytes':123}]}),123)
if __name__=='__main__':unittest.main()
