"""Comparison is a view of stored records, not a new evidence assessment."""
from test_evidence_clarity import render
import pytest

def comparison(html):
    return html.split('<details class="study-comparison">', 1)[1].split('</details>', 1)[0]

def test_both_groups_and_recorded_fields_are_present():
    html = comparison(render(
        evidence=[dict(citation='Primary fixture', study_type='rct', year=2025, n_participants=1234, quality='moderate', pmid='111')],
        counter=[dict(citation='Counter fixture', study_type='meta_analysis', year=2024, n_participants=1234, quality='low', doi='10.1/fixture')]))
    for text in ('Supporting', 'Counter', 'Primary fixture', 'Counter fixture', '2025', '2024', 'meta analysis', 'moderate', 'low'):
        assert text in html
    assert html.count('1,234') == 2 and '2,468' not in html
    assert 'https://pubmed.ncbi.nlm.nih.gov/111/' in html
    assert 'https://doi.org/10.1/fixture' in html
    assert 'scope="col"' in html and 'scope="row"' in html
    assert 'tabindex="0"' in html

def test_empty_and_incomplete_records_are_explicit():
    assert 'No study records available to compare.' in comparison(render())
    html = comparison(render(counter=[{}]))
    assert 'Citation not recorded' in html
    assert html.count('Not recorded') == 4
    assert '>None<' not in html
    assert 'No citation-check detail shown; inspect the source.' in html

@pytest.mark.parametrize('group', ['evidence', 'counter'])
@pytest.mark.parametrize('status', ['flagged', 'citation_mismatch'])
def test_flagged_records_do_not_gain_source_links(group, status):
    html = comparison(render(**{group:[dict(citation='Unsafe fixture',pmid='999',doi='10.1/unsafe',relevance_status=status,is_retracted=True)]}))
    assert 'link suppressed' in html and 'RETRACTED' in html
    assert 'https://pubmed' not in html and 'https://doi.org' not in html

@pytest.mark.parametrize('status', ['flagged', 'citation_mismatch'])
def test_counter_detail_also_suppresses_flagged_link(status):
    html=render(counter=[dict(citation='Flagged counter',pmid='998',doi='10.1/unsafe',relevance_status=status)])
    assert 'https://pubmed.ncbi.nlm.nih.gov/998/' not in html
    assert 'https://doi.org/10.1/unsafe' not in html
    detail=html.split('id="counter-evidence"', 1)[1]
    assert ('CITATION FLAGGED' if status == 'flagged' else 'unverified citation') in detail

def test_text_is_escaped_and_weak_match_is_not_upgraded():
    html=comparison(render(evidence=[dict(citation='<script>bad</script>',relevance_status='weak')]))
    assert '&lt;script&gt;bad&lt;/script&gt;' in html and '<script>' not in html
    assert 'Weak title match' in html
