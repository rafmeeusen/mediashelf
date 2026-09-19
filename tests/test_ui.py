def _make_item(client, **overrides):
    body = {"content_type": "book", "title": "Demon Copperhead", "creator": "Barbara Kingsolver"}
    body.update(overrides)
    return client.post("/items", json=body).json()


def test_index_page_renders(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert "Alle types" in resp.text


def test_search_fragment_filters(client):
    _make_item(client, title="Demon Copperhead")
    _make_item(client, title="Conclaaf", creator="Robert Harris")

    resp = client.get("/ui/items", params={"q": "conclaaf"})
    assert resp.status_code == 200
    assert "Conclaaf" in resp.text
    assert "Demon Copperhead" not in resp.text


def test_detail_page_renders(client):
    item = _make_item(client)
    resp = client.get(f"/ui/items/{item['id']}")
    assert resp.status_code == 200
    assert "Demon Copperhead" in resp.text


def test_detail_page_missing_item_404(client):
    resp = client.get("/ui/items/999")
    assert resp.status_code == 404


def test_rating_field_edit_and_save_accepts_half_point(client):
    item = _make_item(client)

    edit_resp = client.get(f"/ui/items/{item['id']}/fields/rating/edit")
    assert edit_resp.status_code == 200
    assert '<option value="8.5"' in edit_resp.text

    save_resp = client.post(f"/ui/items/{item['id']}/fields/rating", data={"value": "8.5"})
    assert save_resp.status_code == 200
    assert "8.5/10" in save_resp.text

    assert client.get(f"/items/{item['id']}").json()["rating"] == 8.5


def test_rating_field_can_be_cleared(client):
    item = _make_item(client)
    client.post(f"/ui/items/{item['id']}/fields/rating", data={"value": "7"})

    resp = client.post(f"/ui/items/{item['id']}/fields/rating", data={"value": ""})
    assert resp.status_code == 200
    assert client.get(f"/items/{item['id']}").json()["rating"] is None


def test_status_field_edit_and_save(client):
    item = _make_item(client)
    resp = client.post(f"/ui/items/{item['id']}/fields/status", data={"value": "done"})
    assert resp.status_code == 200
    assert "Gedaan" in resp.text
    assert client.get(f"/items/{item['id']}").json()["status"] == "done"


def test_notes_field_edit_and_save(client):
    item = _make_item(client)
    resp = client.post(f"/ui/items/{item['id']}/fields/notes", data={"value": "Goed boek."})
    assert resp.status_code == 200
    assert "Goed boek." in resp.text


def test_unknown_field_404(client):
    item = _make_item(client)
    assert client.get(f"/ui/items/{item['id']}/fields/title").status_code == 404
    assert client.get(f"/ui/items/{item['id']}/fields/title/edit").status_code == 404
    assert client.post(f"/ui/items/{item['id']}/fields/title", data={"value": "x"}).status_code == 404


def test_invalid_rating_value_returns_422(client):
    item = _make_item(client)
    resp = client.post(f"/ui/items/{item['id']}/fields/rating", data={"value": "not-a-number"})
    assert resp.status_code == 422
