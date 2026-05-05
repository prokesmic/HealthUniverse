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
