import pytest
from fastapi.testclient import TestClient

from queenbee_routing.api import DEFAULT_GRAPH_FILE, create_app
from queenbee_routing.dijkstra import dijkstra
from queenbee_routing.graph import Graph

URL = "/api/v1/routing/emergency-path"


@pytest.fixture
def client():
    g = Graph()
    g.add_node("BASE", type="base")
    g.add_node("X1", type="carrefour")
    g.add_node("R1", type="ruche")
    g.add_node("R2", type="ruche")
    g.add_node("R-ISOLEE", type="ruche")
    g.add_edge("BASE", "X1", 5)
    g.add_edge("X1", "R1", 2)
    g.add_edge("BASE", "R1", 10)
    g.add_edge("R1", "R2", 1.5)
    return TestClient(create_app(g))


def test_emergency_path_ok(client):
    response = client.post(URL, json={"start_id": "BASE", "hive_id": "R2"})

    assert response.status_code == 200
    body = response.json()
    assert body["total_cost_min"] == 8.5
    assert body["path"] == ["BASE", "X1", "R1", "R2"]
    assert body["steps"] == 3
    assert body["computation_time_ms"] >= 0


def test_unknown_node_returns_404(client):
    response = client.post(URL, json={"start_id": "BASE", "hive_id": "INCONNUE"})
    assert response.status_code == 404


def test_unreachable_hive_returns_422(client):
    response = client.post(URL, json={"start_id": "BASE", "hive_id": "R-ISOLEE"})
    assert response.status_code == 422


def test_target_must_be_a_hive(client):
    response = client.post(URL, json={"start_id": "BASE", "hive_id": "X1"})
    assert response.status_code == 422


def test_missing_field_returns_422(client):
    response = client.post(URL, json={"start_id": "BASE"})
    assert response.status_code == 422


def test_list_hives(client):
    response = client.get("/api/v1/routing/nodes", params={"type": "ruche"})
    assert {n["id"] for n in response.json()} == {"R1", "R2", "R-ISOLEE"}


def test_every_hive_of_the_real_site_is_reachable():
    g = Graph.from_json_file(DEFAULT_GRAPH_FILE)
    dist, _ = dijkstra(g, "COORD-SN-CASA")
    hives = [n for n, info in g.nodes.items() if info["type"] == "ruche"]
    assert len(hives) == 50
    assert all(h in dist for h in hives)
