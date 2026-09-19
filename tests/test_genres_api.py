def test_create_and_list_genres(client):
    resp = client.post("/genres", json={"name": "Documentary"})
    assert resp.status_code == 201
    assert resp.json()["name"] == "Documentary"

    resp = client.get("/genres")
    assert [g["name"] for g in resp.json()] == ["Documentary"]


def test_duplicate_genre_name_conflicts(client):
    client.post("/genres", json={"name": "Comedy"})
    resp = client.post("/genres", json={"name": "Comedy"})
    assert resp.status_code == 409


def test_delete_genre(client):
    created = client.post("/genres", json={"name": "Drama"}).json()
    resp = client.delete(f"/genres/{created['id']}")
    assert resp.status_code == 204
    assert client.get("/genres").json() == []
