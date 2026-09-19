def test_create_item_manual_defaults_to_to_consume(client):
    resp = client.post(
        "/items",
        json={"content_type": "book", "title": "Schitterend gebrek", "creator": "Arthur Japin"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["status"] == "to_consume"
    assert body["rating"] is None
    assert body["platforms"] == []
    assert body["language"] is None


def test_create_item_with_language_and_source(client):
    language_id = client.post("/languages", json={"name": "Engels"}).json()["id"]
    resp = client.post(
        "/items",
        json={
            "content_type": "book",
            "title": "Demon Copperhead",
            "creator": "Barbara Kingsolver",
            "language_id": language_id,
            "source": "De Standaard artikel over oxycodon",
        },
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["language"]["name"] == "Engels"
    assert body["source"] == "De Standaard artikel over oxycodon"


def test_rating_out_of_range_rejected(client):
    resp = client.post(
        "/items",
        json={"content_type": "book", "title": "Bad rating", "rating": 11},
    )
    assert resp.status_code == 422


def test_patch_marks_item_done_with_rating_and_notes(client):
    item = client.post("/items", json={"content_type": "movie", "title": "The Quiet Girl"}).json()

    resp = client.patch(
        f"/items/{item['id']}",
        json={
            "status": "done",
            "rating": 8,
            "notes": "wou ik in cinema gaan zien, maar niet van gek",
            "completed_date": "2024-04-12",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "done"
    assert body["rating"] == 8
    assert body["completed_date"] == "2024-04-12"


def test_list_items_filters_by_status_and_content_type(client):
    client.post("/items", json={"content_type": "book", "title": "To read"})
    done_item = client.post("/items", json={"content_type": "movie", "title": "Watched"}).json()
    client.patch(f"/items/{done_item['id']}", json={"status": "done"})

    resp = client.get("/items", params={"status": "done"})
    assert [i["title"] for i in resp.json()] == ["Watched"]

    resp = client.get("/items", params={"content_type": "book"})
    assert [i["title"] for i in resp.json()] == ["To read"]


def test_get_missing_item_404(client):
    resp = client.get("/items/999")
    assert resp.status_code == 404


def test_delete_item(client):
    item = client.post("/items", json={"content_type": "podcast", "title": "Nerdland"}).json()
    resp = client.delete(f"/items/{item['id']}")
    assert resp.status_code == 204
    assert client.get(f"/items/{item['id']}").status_code == 404
