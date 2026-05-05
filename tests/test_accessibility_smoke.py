from fastapi.testclient import TestClient

from web.app import app


client = TestClient(app)


def test_core_pages_render():
    for path in ["/", "/tier/A", "/category/nutrition", "/discoveries", "/me", "/explore"]:
        response = client.get(path)
        assert response.status_code == 200, path


def test_skip_link_and_search_labels_present():
    response = client.get("/")
    body = response.text
    assert 'href="#main-content"' in body
    assert 'aria-label="Site search"' in body
    assert 'id="main-content"' in body


def test_search_page_has_programmatic_label():
    response = client.get("/search", params={"q": "magnesium"})
    body = response.text
    assert response.status_code == 200
    assert 'for="search-page-query"' in body
    assert 'id="search-page-query"' in body
