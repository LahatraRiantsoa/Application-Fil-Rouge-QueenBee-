"""
Graphe de référence, calculable à la main :

        A ---4--- B
        |       / |
        1     2   1
        |   /     |
        C ---5--- D ---3--- E

    F ---2--- G        (composante isolée : inaccessible depuis A)

Plus court chemin A -> E : A -1- C -2- B -1- D -3- E = 7
(le chemin « direct » A -4- B -1- D -3- E coûte 8 : le détour par C est meilleur)
"""

import random

import pytest

from queenbee_routing.dijkstra import NoPathError, NodeNotFoundError, dijkstra, shortest_path
from queenbee_routing.dijkstra_naive import dijkstra_naive
from queenbee_routing.generator import dense_graph, sparse_graph
from queenbee_routing.graph import Graph

ALGORITHMS = [dijkstra, dijkstra_naive]


@pytest.fixture
def graph():
    g = Graph()
    g.add_edge("A", "B", 4)
    g.add_edge("A", "C", 1)
    g.add_edge("C", "B", 2)
    g.add_edge("B", "D", 1)
    g.add_edge("C", "D", 5)
    g.add_edge("D", "E", 3)
    g.add_edge("F", "G", 2)
    return g


def assert_valid_path(graph, path, cost):
    """Le chemin doit suivre des arêtes existantes et son coût doit être `cost`."""
    total = 0
    for u, v in zip(path, path[1:]):
        weights = [w for neighbor, w in graph.neighbors(u) if neighbor == v]
        assert weights, f"pas d'arête {u} -> {v}"
        total += min(weights)
    assert total == pytest.approx(cost)


# --- Cas normaux --------------------------------------------------------------

@pytest.mark.parametrize("algorithm", ALGORITHMS)
def test_hand_computed_shortest_path(graph, algorithm):
    cost, path = shortest_path(graph, "A", "E", algorithm)
    assert cost == 7
    assert path == ["A", "C", "B", "D", "E"]


@pytest.mark.parametrize("algorithm", ALGORITHMS)
def test_all_distances_from_source(graph, algorithm):
    dist, _ = algorithm(graph, "A")
    assert dist == {"A": 0, "C": 1, "B": 3, "D": 4, "E": 7}


def test_directed_edge_is_one_way():
    g = Graph()
    g.add_edge("A", "B", 1, directed=True)
    assert shortest_path(g, "A", "B") == (1, ["A", "B"])
    with pytest.raises(NoPathError):
        shortest_path(g, "B", "A")


# --- Cas limites --------------------------------------------------------------

@pytest.mark.parametrize("algorithm", ALGORITHMS)
def test_source_equals_target(graph, algorithm):
    assert shortest_path(graph, "B", "B", algorithm) == (0, ["B"])


@pytest.mark.parametrize("algorithm", ALGORITHMS)
def test_unreachable_target_in_disconnected_graph(graph, algorithm):
    with pytest.raises(NoPathError):
        shortest_path(graph, "A", "G", algorithm)


@pytest.mark.parametrize("algorithm", ALGORITHMS)
def test_unknown_source(graph, algorithm):
    with pytest.raises(NodeNotFoundError):
        shortest_path(graph, "Z", "A", algorithm)


def test_unknown_target(graph):
    with pytest.raises(NodeNotFoundError):
        shortest_path(graph, "A", "Z")


def test_isolated_node():
    g = Graph()
    g.add_node("SEUL")
    assert dijkstra(g, "SEUL") == ({"SEUL": 0}, {"SEUL": None})


@pytest.mark.parametrize("algorithm", ALGORITHMS)
def test_graph_with_cycle(algorithm):
    # Cycle A -> B -> C -> D -> A : l'algorithme ne doit pas boucler à l'infini.
    g = Graph()
    for u, v in [("A", "B"), ("B", "C"), ("C", "D"), ("D", "A")]:
        g.add_edge(u, v, 1)
    cost, path = shortest_path(g, "A", "C", algorithm)
    assert cost == 2
    assert path in (["A", "B", "C"], ["A", "D", "C"])


@pytest.mark.parametrize("algorithm", ALGORITHMS)
def test_equal_cost_paths(algorithm):
    g = Graph()
    g.add_edge("S", "X", 2)
    g.add_edge("S", "Y", 2)
    g.add_edge("X", "T", 3)
    g.add_edge("Y", "T", 3)
    cost, path = shortest_path(g, "S", "T", algorithm)
    assert cost == 5
    assert path in (["S", "X", "T"], ["S", "Y", "T"])


def test_zero_weight_edge():
    g = Graph()
    g.add_edge("A", "B", 0)
    g.add_edge("B", "C", 1)
    assert shortest_path(g, "A", "C") == (1, ["A", "B", "C"])


def test_parallel_edges_keep_the_cheapest():
    g = Graph()
    g.add_edge("A", "B", 10)
    g.add_edge("A", "B", 3)
    assert shortest_path(g, "A", "B") == (3, ["A", "B"])


def test_negative_weight_is_rejected():
    with pytest.raises(ValueError):
        Graph().add_edge("A", "B", -1)


# --- Comparaison avec la version naïve sur des graphes aléatoires -------------

@pytest.mark.parametrize("seed", range(10))
def test_heap_and_naive_versions_agree(seed):
    rng = random.Random(seed)
    g = sparse_graph(200, avg_degree=4, seed=seed) if seed % 2 else dense_graph(80, seed=seed)
    source = rng.choice(list(g.adjacency))

    dist_heap, prev_heap = dijkstra(g, source)
    dist_naive, _ = dijkstra_naive(g, source)

    assert dist_heap == dist_naive
    for target in rng.sample(list(dist_heap), 10):
        cost, path = shortest_path(g, source, target)
        assert_valid_path(g, path, cost)
