def _make_item(client, content_type="movie", title="Fiore mio"):
    return client.post("/items", json={"content_type": content_type, "title": title}).json()


def test_add_and_remove_genre(client):
    item = _make_item(client)
    genre = client.post("/genres", json={"name": "Documentary"}).json()

    resp = client.post(f"/items/{item['id']}/genres/{genre['id']}")
    assert resp.status_code == 200
    assert [g["name"] for g in resp.json()["genres"]] == ["Documentary"]

    resp = client.delete(f"/items/{item['id']}/genres/{genre['id']}")
    assert resp.status_code == 200
    assert resp.json()["genres"] == []


def test_item_can_have_multiple_genres(client):
    item = _make_item(client)
    doc = client.post("/genres", json={"name": "Documentary"}).json()
    comedy = client.post("/genres", json={"name": "Comedy"}).json()

    client.post(f"/items/{item['id']}/genres/{doc['id']}")
    resp = client.post(f"/items/{item['id']}/genres/{comedy['id']}")

    assert sorted(g["name"] for g in resp.json()["genres"]) == ["Comedy", "Documentary"]


def test_adding_same_genre_twice_is_idempotent(client):
    item = _make_item(client)
    genre = client.post("/genres", json={"name": "Comedy"}).json()

    client.post(f"/items/{item['id']}/genres/{genre['id']}")
    resp = client.post(f"/items/{item['id']}/genres/{genre['id']}")
    assert resp.status_code == 200
    assert [g["name"] for g in resp.json()["genres"]] == ["Comedy"]


def test_add_missing_genre_404(client):
    item = _make_item(client)
    resp = client.post(f"/items/{item['id']}/genres/999")
    assert resp.status_code == 404


def test_remove_genre_not_linked_404(client):
    item = _make_item(client)
    genre = client.post("/genres", json={"name": "Comedy"}).json()
    resp = client.delete(f"/items/{item['id']}/genres/{genre['id']}")
    assert resp.status_code == 404


def test_filter_items_by_genre(client):
    documentary = client.post("/genres", json={"name": "Documentary"}).json()
    doc_item = _make_item(client, title="No Other Land")
    _make_item(client, title="C'mon C'mon")
    client.post(f"/items/{doc_item['id']}/genres/{documentary['id']}")

    resp = client.get("/items", params={"genre": "documentary"})
    assert [i["title"] for i in resp.json()] == ["No Other Land"]
