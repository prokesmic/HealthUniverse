from __future__ import annotations


def test_routes_return_200_with_empty_db(client):
    assert client.get("/").status_code == 200
    assert client.get("/tier/A").status_code == 200
    assert client.get("/category/nutrition").status_code == 200
    assert client.get("/search?q=magnesium").status_code == 200
    assert client.get("/sitemap.xml").status_code == 200
    assert client.get("/robots.txt").status_code == 200


def test_routes_return_200_with_seeded_db(client, seeded_edge):
    home = client.get("/")
    assert home.status_code == 200
    assert "Magnesium" in home.text

    search = client.get("/search?q=magnesium")
    assert search.status_code == 200
    assert "Magnesium" in search.text

    edge = client.get(f"/edge/{seeded_edge}")
    assert edge.status_code == 200
    assert "Sleep quality" in edge.text

    card = client.get(f"/edge/{seeded_edge}.png")
    assert card.status_code == 200
    assert card.headers["content-type"] == "image/png"
