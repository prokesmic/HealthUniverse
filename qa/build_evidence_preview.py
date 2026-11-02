"""Local synthetic preview; never loads application DB or secrets."""
import importlib.util
from pathlib import Path

root = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('clarity', root / 'tests/test_evidence_clarity.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
body = m.render(population='Adults in a synthetic example', effect='Not estimated in this demonstration', retracted=1,
    evidence=[dict(citation='Synthetic primary study — shared cohort', n_participants=1234, study_type='rct', year=2025, quality='moderate'),
              dict(citation='Synthetic review — includes that cohort', n_participants=1234, study_type='meta_analysis', year=2026, quality='low', is_retracted=True)],
    counter=[dict(citation='Synthetic counter-evidence', study_type='rct', year=2026, notes='Fixture only; not a medical claim.')])
body = body.replace('href="/static/', 'href="../web/static/')
out = root / 'qa/evidence-clarity-preview.html'
out.write_text('<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>HealthUniverse — synthetic preview</title><link rel="stylesheet" href="../web/static/style.css"><body><main id="main-content"><p style="padding:16px">LOCAL SYNTHETIC PREVIEW — no real medical claims</p>' + body + '</main></body></html>')
print(out)
