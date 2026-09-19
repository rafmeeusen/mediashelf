def test_create_and_list_languages(client):
    resp = client.post("/languages", json={"name": "Nederlands"})
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "Nederlands"

    resp = client.get("/languages")
    assert resp.status_code == 200
    assert [lang["name"] for lang in resp.json()] == ["Nederlands"]


def test_duplicate_language_name_conflicts(client):
    client.post("/languages", json={"name": "Engels"})
    resp = client.post("/languages", json={"name": "Engels"})
    assert resp.status_code == 409


def test_delete_language(client):
    created = client.post("/languages", json={"name": "Frans"}).json()
    resp = client.delete(f"/languages/{created['id']}")
    assert resp.status_code == 204
    assert client.get("/languages").json() == []


def test_delete_missing_language_404(client):
    resp = client.delete("/languages/999")
    assert resp.status_code == 404
