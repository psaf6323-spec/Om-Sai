"""Run the Om Sai test phases. Needs: pip install -r tests/requirements.txt && playwright install chromium
Usage: python3 tests/run_all.py          (quick: ~3 min)
       python3 tests/run_all.py --full   (adds the 1000-item photo run, ~3 more min)"""
import subprocess, sys, os
here = os.path.dirname(os.path.abspath(__file__))
phases = ['phase1.py', 'phase2.py', 'phase3.py', 'phase6.py', 'phase7.py', 'phase8.py', 'phase9.py'] + (['phase5.py'] if '--full' in sys.argv else [])
bad = 0
for p in phases:
    print(f'\n=== {p}'); r = subprocess.run([sys.executable, p], cwd=here, capture_output=True, text=True)
    out = r.stdout + r.stderr; print(out[-1800:])
    if r.returncode != 0 or 'FAIL' in out.replace('PASS', ''): bad += 1
print('\nALL PHASES CLEAN' if not bad else f'\n{bad} phase(s) need attention'); sys.exit(1 if bad else 0)
