"""
Algorithme de Dijkstra avec file de priorité (tas binaire maison).

Principe : on « explore » les sommets du plus proche au plus éloigné de la
source. Le tas donne à chaque tour le sommet non encore visité de plus petite
distance provisoire. Quand un sommet sort du tas pour la première fois, sa
distance est définitive (c'est ce qui exige des poids positifs).

Complexité : O((|V| + |E|) log |V|), voir README.md section 9.
"""

from .min_heap import MinHeap


class NodeNotFoundError(Exception):
    """Le sommet demandé n'existe pas dans le graphe."""


class NoPathError(Exception):
    """Aucun chemin ne relie la source à la cible (graphe non connexe)."""


def dijkstra(graph, source, target=None):
    """
    Calcule les plus courtes distances depuis `source`.

    Si `target` est donné, on s'arrête dès que la cible est atteinte
    (arrêt anticipé : inutile d'explorer tout le site pour une urgence).

    Renvoie (dist, prev) :
      - dist[x] = coût minimal de source à x (seulement pour les sommets atteints)
      - prev[x] = sommet précédent x sur ce chemin (None pour la source)
    """
    if source not in graph:
        raise NodeNotFoundError(source)

    dist = {source: 0}
    prev = {source: None}
    visited = set()

    heap = MinHeap()
    heap.push(0, source)

    while not heap.is_empty():
        d, u = heap.pop()

        # Un même sommet peut être dans le tas plusieurs fois (avec d'anciennes
        # distances plus grandes). On ignore ces entrées périmées :
        # c'est la « suppression paresseuse » (lazy deletion).
        if u in visited:
            continue
        visited.add(u)

        if u == target:
            break

        # Relaxation : passer par u améliore-t-il la distance vers v ?
        for v, weight in graph.neighbors(u):
            if v in visited:
                continue
            new_dist = d + weight
            if v not in dist or new_dist < dist[v]:
                dist[v] = new_dist
                prev[v] = u
                heap.push(new_dist, v)

    return dist, prev


def reconstruct_path(prev, target):
    """Remonte les prédécesseurs depuis la cible, puis inverse la liste."""
    path = []
    node = target
    while node is not None:
        path.append(node)
        node = prev[node]
    path.reverse()
    return path


def shortest_path(graph, source, target, algorithm=dijkstra):
    """
    Renvoie (coût_total, chemin) entre source et target.

    `algorithm` permet de brancher la version naïve pour la comparer.
    """
    if target not in graph:
        raise NodeNotFoundError(target)
    dist, prev = algorithm(graph, source, target)
    if target not in dist:
        raise NoPathError(f"aucun chemin entre {source} et {target}")
    return dist[target], reconstruct_path(prev, target)
