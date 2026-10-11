#!/usr/bin/env python3
"""Publish the audited native two-class pass; historical report source is archived."""
import runpy
import sys
from pathlib import Path
if len(sys.argv)>1:
    raise SystemExit('Run tools/pass6_report.py on the test-host results layout. Historical report source: results/pass5/prior/report-pre-pass5.py')
runpy.run_path(str(Path(__file__).with_name('pass6_report.py')),run_name='__main__')
