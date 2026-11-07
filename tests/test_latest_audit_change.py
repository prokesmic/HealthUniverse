from web.app import _classify_event
from web.audit_display import latest_recorded_change
from jinja2 import Environment, FileSystemLoader
from pathlib import Path
import pytest

def event(id=1, date='2026-10-01', field='tier', old='C', new='B', reason='Fixture reason'):
    return _classify_event(dict(id=id, changed_at=date, field=field, old_value=old, new_value=new, reason=reason))

def panel(result):
    env=Environment(loader=FileSystemLoader(Path(__file__).resolve().parents[1]/'web/templates'),autoescape=True)
    return env.get_template('_latest_audit_change.html').render(latest_change=result)

def test_latest_dated_change_is_separate_from_newer_prose():
    rows=[event(id=2,date='2026-11-01',field='summary'),event(id=1),event(id=3,date='2026-10-20',field='retraction')]
    result=latest_recorded_change(rows)
    assert result['change']['raw']['id']==3
    assert result['prose']['raw']['id']==2
    html=panel(result)
    assert 'href="#audit-event-3"' in html
    assert '2026-10-20' in html and '2026-11-01' in html

@pytest.mark.parametrize('date',[None,'','2026-11','invalid','2026-02-30'])
def test_unknown_dates_are_never_presented_as_latest(date):
    result=latest_recorded_change([event(date=date)])
    assert result['change'] is None and result['undated']==1
    assert 'missing or invalid date' in panel(result)
    assert 'href="#audit-event-1"' in panel(result)

def test_empty_and_prose_only_do_not_claim_stability():
    for rows in ([],[event(field='summary')]):
        html=panel(latest_recorded_change(rows))
        assert 'does not establish that the evidence is unchanged' in html
    assert 'text update alone' in panel(latest_recorded_change([event(field='summary')]))

def test_same_tier_not_a_change_and_dates_normalize_timezones():
    assert latest_recorded_change([event(old='B',new='B')])['change'] is None
    result=latest_recorded_change([event(id=1,date='2026-10-01T10:00:00+02:00'),event(id=2,date='2026-10-01T09:00:00Z')])
    assert result['change']['raw']['id']==2

def test_equal_date_choice_is_stable_and_missing_id_has_no_broken_link():
    a,b=event(id=1),event(id=2)
    assert latest_recorded_change([a,b])['change']==latest_recorded_change([b,a])['change']
    assert '#audit-event-None' not in panel(latest_recorded_change([event(id=None)]))

def test_route_source_anchor_and_tier_transition(client,seeded,tmpdb):
    db,eid=tmpdb,seeded['edge_id']
    with db.connect() as conn:
        row=conn.execute("INSERT INTO edge_history(edge_id,field,old_value,new_value,reason,changed_at) VALUES(?, 'tier','C','B','Fixture reason','2026-10-01')",(eid,))
        event_id=row.lastrowid
    html=client.get(f'/edge/{eid}').text
    assert 'Recorded tier: C → B' in html
    assert f'href="#audit-event-{event_id}"' in html
    assert f'id="audit-event-{event_id}"' in html
