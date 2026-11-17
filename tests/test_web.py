def test_routes_empty_db_200(client):
    for path in ("/", "/discoveries", "/myths", "/changes", "/me",
                 "/search?q=test", "/tier/A", "/category/nutrition",
                 "/sitemap.xml", "/robots.txt"):
        r = client.get(path)
        assert r.status_code == 200, f"{path} -> {r.status_code}"


def test_routes_seeded_db(client, seeded):
    home = client.get("/")
    assert home.status_code == 200
    assert "Magnesium" in home.text or "Sleep quality" in home.text

    edge = client.get(f"/edge/{seeded['edge_id']}")
    assert edge.status_code == 200
    assert "Sleep quality" in edge.text
    assert "Magnesium" in edge.text


def test_edge_png(client, seeded):
    r = client.get(f"/edge/{seeded['edge_id']}.png")
    assert r.status_code == 200
    assert r.headers["content-type"] == "image/png"
    assert len(r.content) > 1000


def test_api_edges_json(client, seeded):
    r = client.get("/api/edges?tier=B&limit=10")
    assert r.status_code == 200
    data = r.json()
    assert data["count"] >= 1
    assert data["edges"][0]["tier"] == "B"
    assert data["edges"][0]["factor_name"] == "Magnesium"


def test_api_entity_json(client, seeded):
    r = client.get("/api/entities/magnesium")
    assert r.status_code == 200
    d = r.json()
    assert d["entity"]["slug"] == "magnesium"
    assert len(d["as_factor"]) == 1


def test_api_entity_404(client):
    r = client.get("/api/entities/this_does_not_exist")
    assert r.status_code == 404


def test_condition_quickpicks_lead_with_general_conditions_including_cancer():
    """17.11.2026: the chips were 'most A/B edges', so Cancer never showed."""
    import sqlite3
    from web import app as webapp
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript("""
      CREATE TABLE entity (id INTEGER PRIMARY KEY, slug TEXT, name TEXT, kind TEXT);
      CREATE TABLE edge (id INTEGER PRIMARY KEY, outcome_id INT, tier TEXT);
      INSERT INTO entity VALUES (1,'cancer_incidence','Cancer incidence','process'),
        (2,'cvd','Cardiovascular disease','condition'), (3,'falls','Falls','condition'),
        (4,'overall_clinical_outcomes','Overall clinical outcomes','outcome'),
        (5,'mortality','Mortality','condition'), (6,'lung_cancer','Lung cancer','condition');
    """)
    conn.executemany("INSERT INTO edge (outcome_id, tier) VALUES (?, 'A')",
                     [(3,)] * 50 + [(4,)] * 40 + [(5,)] * 30 + [(6,)] * 5 + [(2,)] * 2)
    picks = webapp.quickpick_conditions(conn)
    assert [p["name"] for p in picks] == ["Cancer (any type)", "Cardiovascular disease", "Falls", "Lung cancer"]
    assert [p["general"] for p in picks] == [True, True, False, False]


def test_cancer_means_every_cancer_but_counts_once(monkeypatch):
    """17.11.2026: picking "Cancer" covers colorectal, breast, lung … ; the
    form, labels and cookie keep the one choice, and overlap counts it once."""
    import profile as prof
    assert prof.is_cancer("colorectal_cancer", "Colorectal cancer")
    assert prof.is_cancer("non_hodgkin_lymphoma", "Non-Hodgkin lymphoma")
    assert not prof.is_cancer("cancer_detection_rate", "Cancer detection rate")
    assert not prof.is_cancer("cvd", "Cardiovascular disease")
    monkeypatch.setitem(prof.CONDITION_GROUPS, "cancer_incidence", lambda: ("colorectal_cancer", "breast_cancer"))
    p = prof.Profile(conditions=["cancer_incidence", "cvd"])
    assert p.conditions == ["cancer_incidence", "cvd"]
    assert p.condition_slugs == ["cancer_incidence", "colorectal_cancer", "breast_cancer", "cvd"]
    assert prof.picked_condition_for("breast_cancer", p.conditions) == "cancer_incidence"
    assert prof.picked_condition_for("cvd", p.conditions) == "cvd"
    assert '"breast_cancer"' not in prof._unsign(prof.encode(p)).decode()          # cookie keeps the choice
    assert prof.relevance_score({"o_slug": "breast_cancer", "tier": "D"}, p) > \
        prof.relevance_score({"o_slug": "lung_cancer", "tier": "D"}, p)
