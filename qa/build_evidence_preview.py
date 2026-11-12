"""Local synthetic preview; never loads application DB or secrets."""
import importlib.util
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))
spec = importlib.util.spec_from_file_location('clarity', root / 'tests/test_evidence_clarity.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
body = m.render(population='Adults in a synthetic example', effect='Not estimated in this demonstration', retracted=1,
    audit_events=[dict(category='tier_promotion', headline='Synthetic tier change to B', changed_at='2026-10-20', old_value='C', new_value='B', raw=dict(id=99, field='tier'), detail='Fixture reason only; not a real reassessment.', is_meaningful=True, agent_label='Synthetic fixture'),
                  dict(category='prose', headline='Synthetic text update', changed_at='2026-11-01', raw=dict(id=100, field='summary'), is_meaningful=False, agent_label='Synthetic fixture')],
    evidence=[dict(citation='Synthetic primary study — shared cohort', n_participants=1234, study_type='rct', year=2025, quality='moderate'),
              dict(citation='Synthetic review — includes that cohort', n_participants=1234, study_type='meta_analysis', year=2026, quality='low', is_retracted=True)],
    counter=[dict(citation='Synthetic counter-evidence', study_type='rct', year=2026, notes='Fixture only; not a medical claim.')])
body = body.replace('href="/static/', 'href="../web/static/')
out = root / 'qa/evidence-clarity-preview.html'
out.write_text('<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>HealthUniverse — synthetic preview</title><link rel="stylesheet" href="../web/static/style.css"><body><main id="main-content"><p style="padding:16px">LOCAL SYNTHETIC PREVIEW — no real medical claims</p>' + body + '</main></body></html>')
print(out)
