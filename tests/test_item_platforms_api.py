def _make_item(client):
    return client.post("/items", json={"content_type": "book", "title": "Mislukte staten"}).json()


def test_link_item_to_platforms_with_availability(client):
    item = _make_item(client)
    leuven = client.post("/platforms", json={"name": "bib leuven"}).json()
    cloudlib = client.post("/platforms", json={"name": "cloudlib"}).json()

    resp = client.put(f"/items/{item['id']}/platforms/{leuven['id']}", json={"available": True})
    assert resp.status_code == 200
    resp = client.put(f"/items/{item['id']}/platforms/{cloudlib['id']}", json={"available": False})
    assert resp.status_code == 200

    body = client.get(f"/items/{item['id']}").json()
    by_name = {p["platform"]: p["available"] for p in body["platforms"]}
    assert by_name == {"bib leuven": True, "cloudlib": False}


def test_relinking_platform_flips_availability(client):
    item = _make_item(client)
    platform = client.post("/platforms", json={"name": "bib leuven"}).json()

    client.put(f"/items/{item['id']}/platforms/{platform['id']}", json={"available": True})
    client.put(f"/items/{item['id']}/platforms/{platform['id']}", json={"available": False})

    body = client.get(f"/items/{item['id']}").json()
    assert body["platforms"] == [{"platform_id": platform["id"], "platform": "bib leuven", "available": False}]


def test_link_to_missing_platform_404(client):
    item = _make_item(client)
    resp = client.put(f"/items/{item['id']}/platforms/999", json={"available": True})
    assert resp.status_code == 404


def test_remove_platform_link(client):
    item = _make_item(client)
    platform = client.post("/platforms", json={"name": "bib leuven"}).json()
    client.put(f"/items/{item['id']}/platforms/{platform['id']}", json={"available": True})

    resp = client.delete(f"/items/{item['id']}/platforms/{platform['id']}")
    assert resp.status_code == 200
    assert resp.json()["platforms"] == []

    resp = client.delete(f"/items/{item['id']}/platforms/{platform['id']}")
    assert resp.status_code == 404
