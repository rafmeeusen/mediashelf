def test_create_and_list_platforms(client):
    resp = client.post("/platforms", json={"name": "bib leuven"})
    assert resp.status_code == 201
    assert resp.json()["name"] == "bib leuven"

    resp = client.get("/platforms")
    assert [p["name"] for p in resp.json()] == ["bib leuven"]


def test_duplicate_platform_name_conflicts(client):
    client.post("/platforms", json={"name": "cloudlib"})
    resp = client.post("/platforms", json={"name": "cloudlib"})
    assert resp.status_code == 409


def test_delete_platform(client):
    created = client.post("/platforms", json={"name": "cinema"}).json()
    resp = client.delete(f"/platforms/{created['id']}")
    assert resp.status_code == 204
    assert client.get("/platforms").json() == []
