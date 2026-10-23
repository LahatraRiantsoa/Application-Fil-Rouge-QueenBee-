"""
Graphe pondéré représenté par listes d'adjacence.

    adjacency = {
        "A": [("B", 4.0), ("C", 1.0)],   # depuis A on peut aller en B (4 min) ou en C (1 min)
        "B": [("A", 4.0)],
        ...
    }

Les listes d'adjacence sont adaptées à un réseau de pistes : chaque point n'est
relié qu'à quelques voisins (graphe « creux »), donc on ne stocke que les
arêtes qui existent, en mémoire O(|V| + |E|).
"""

import json


class Graph:
    def __init__(self):
        self.adjacency = {}  # identifiant -> liste de (voisin, poids)
        self.nodes = {}      # identifiant -> informations (type, lat, lon...)
        self._edge_count = 0

    def add_node(self, node_id, **info):
        if node_id not in self.adjacency:
            self.adjacency[node_id] = []
            self.nodes[node_id] = {}
        self.nodes[node_id].update(info)

    def add_edge(self, u, v, weight, directed=False):
        """Ajoute une arête u -> v (et v -> u si le graphe est non orienté)."""
        # Dijkstra n'est correct qu'avec des poids positifs ou nuls :
        # on refuse dès la construction tout poids négatif.
        if weight < 0:
            raise ValueError(f"poids négatif interdit : {u} -> {v} = {weight}")
        self.add_node(u)
        self.add_node(v)
        self.adjacency[u].append((v, weight))
        if not directed:
            self.adjacency[v].append((u, weight))
        self._edge_count += 1

    def neighbors(self, node_id):
        return self.adjacency[node_id]

    def __contains__(self, node_id):
        # Permet d'écrire : if "A" in graph
        return node_id in self.adjacency

    def node_count(self):
        return len(self.adjacency)

    def edge_count(self):
        return self._edge_count

    # --- Lecture / écriture JSON -------------------------------------------

    @classmethod
    def from_dict(cls, data):
        graph = cls()
        for node in data["nodes"]:
            info = {key: value for key, value in node.items() if key != "id"}
            graph.add_node(node["id"], **info)
        for edge in data["edges"]:
            graph.add_edge(edge["from"], edge["to"], edge["time_min"])
        return graph

    @classmethod
    def from_json_file(cls, path):
        with open(path, encoding="utf-8") as f:
            return cls.from_dict(json.load(f))
