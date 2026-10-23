"""
Version naïve de Dijkstra, SANS tas : O(|V|²).

À chaque tour, on cherche le sommet non visité de plus petite distance en
parcourant TOUS les sommets (O(|V|)). Comme il y a |V| tours : O(|V|²).

Elle sert uniquement de référence pour le benchmark et pour vérifier,
dans les tests, que la version avec tas donne les mêmes résultats.
"""

from .dijkstra import NodeNotFoundError

INFINITY = float("inf")


def dijkstra_naive(graph, source, target=None):
    """Même interface que dijkstra() : renvoie (dist, prev) des sommets atteints."""
    if source not in graph:
        raise NodeNotFoundError(source)

    dist = {node: INFINITY for node in graph.adjacency}
    prev = {node: None for node in graph.adjacency}
    dist[source] = 0
    visited = set()

    for _ in range(len(dist)):
        # Recherche linéaire du minimum : c'est elle qui coûte O(|V|) par tour.
        u = None
        best = INFINITY
        for node, d in dist.items():
            if node not in visited and d < best:
                u = node
                best = d

        if u is None:  # les sommets restants sont inaccessibles
            break
        visited.add(u)
        if u == target:
            break

        for v, weight in graph.neighbors(u):
            if v not in visited and best + weight < dist[v]:
                dist[v] = best + weight
                prev[v] = u

    # On ne garde que les sommets atteints, comme dijkstra().
    reached = {node: d for node, d in dist.items() if d < INFINITY}
    return reached, {node: prev[node] for node in reached}
