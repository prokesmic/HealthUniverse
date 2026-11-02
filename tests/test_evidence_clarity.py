"""Render real dossier template using synthetic evidence, without a database."""
from pathlib import Path
from jinja2 import Environment, ChoiceLoader, DictLoader, FileSystemLoader
import pytest

def render(status='verified_evidence', evidence=None, counter=None, population='', effect='', retracted=0):
    env = Environment(loader=ChoiceLoader([
        DictLoader({'base.html': '{% block content %}{% endblock %}'}),
        FileSystemLoader(Path(__file__).resolve().parents[1] / 'web/templates')
    ]), autoescape=True)
    e = dict(id=1, f_name='Example factor', o_name='Example outcome',
             tier='B', direction='neutral', review_status=status, population=population,
             effect_quant=effect, last_reviewed='2026-11-02', seed_source='fixture',
             summary='Synthetic claim', f_slug='factor', o_slug='outcome')
    audit = dict(n_studies=0, days_stable=None, days_since_study=None, days_since_review=None)
    return env.get_template('edge.html').render(
        e=e, evidence=evidence or [], counter=counter or [], audit_summary=audit,
        retracted_evidence_count=retracted, profile=None,
        TIER_LABEL={'B':'Moderate'}, TIER_DOTS={'B':3}, DIRECTION_LABEL={'neutral':'Neutral'})

def test_title_match_does_not_claim_conclusion_verified():
    html = render()
    assert 'Citation title matched' in html
    assert 'does not establish that the study supports the conclusion' in html
    assert 'Evidence verified' not in html

@pytest.mark.parametrize('status,label', [
    ('unreviewed','Machine-generated, unaudited'), ('needs_recheck','Needs recheck'),
    ('human_reviewed','Human-reviewed'), ('clinician_reviewed','Clinician-reviewed')])
def test_other_review_states_are_preserved(status,label):
    html=render(status=status)
    assert label in html
    assert 'Citation title matched' not in html

def test_overlapping_studies_keep_individual_counts_without_total():
    studies=[dict(citation='Same cohort primary', n_participants=1234, study_type='rct'),
             dict(citation='Review including same cohort', n_participants=1234, study_type='meta_analysis')]
    html=render(evidence=studies)
    assert html.count('n=1,234') == 2
    assert '2,468' not in html
    assert '<dt>Participants</dt>' not in html
    assert 'overlapping participants' in html

def test_missing_data_stays_explicit_and_counter_absence_is_not_proof():
    html=render()
    assert 'applicability is unknown' in html
    assert 'No quantitative effect recorded' in html
    assert 'does not establish that none exists' in html

def test_populated_data_counter_link_and_escaping():
    html=render(population='<script>example</script>',effect='Fixture estimate',counter=[dict(citation='Counter study')])
    assert '&lt;script&gt;example&lt;/script&gt;' in html
    assert 'Fixture estimate' in html
    assert 'href="#counter-evidence"' in html and 'id="counter-evidence"' in html
    assert 'No counter-evidence is recorded' not in html

def test_retraction_warning_stays_ahead_of_context_and_flagged_links_suppressed():
    html=render(retracted=1,evidence=[dict(citation='Flagged study',pmid='999999999',is_retracted=True,relevance_status='flagged')])
    assert html.index('Retraction warning') < html.index('How to read this claim')
    assert 'CITATION FLAGGED' in html and 'RETRACTED' in html
    assert 'https://pubmed.ncbi.nlm.nih.gov/999999999/' not in html
