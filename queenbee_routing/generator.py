"""
Génération des graphes utilisés par le projet.

1. generate_site() : réseau de pistes réaliste d'un site rucher QueenBee.
   Le cahier des charges ne fournit pas de réseau routier : on le modélise.
     - 1 base du coordinateur régional (point de départ)
     - des carrefours (croisements de pistes)
     - 50 ruches (400 ruches / 8 sites, CDC §1.4), identifiants au format
       du CDC §6.5 : "SN-CASA-014"
   Poids d'une arête = temps de trajet en minutes
                     = distance (km) / vitesse (km/h) * 60
   La vitesse dépend du type de voie (route, piste, sentier).

2. sparse_graph() / dense_graph() : graphes aléatoires pour le benchmark.

Lancer `python -m queenbee_routing.generator` régénère data/site_sn_casa.json.
"""

import json
import math
import random
from pathlib import Path

from .graph import Graph

EARTH_RADIUS_KM = 6371.0

# Vitesses moyennes estimées en zone rurale (km/h).
ROAD_SPEEDS_KMH = {"route": 50, "piste": 25, "sentier": 5}

# Une piste n'est jamais en ligne droite : on majore la distance à vol d'oiseau.
SINUOSITY = 1.3


def haversine_km(lat1, lon1, lat2, lon2):
    """Distance à vol d'oiseau entre deux points GPS (formule de Haversine)."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))


def _random_point(rng, center_lat, center_lon, radius_km):
    """Point aléatoire dans un disque de rayon radius_km autour du centre."""
    r = radius_km * math.sqrt(rng.random())  # sqrt : répartition uniforme dans le disque
    angle = rng.uniform(0, 2 * math.pi)
    dlat = (r * math.cos(angle)) / 111.0  # 1 degré de latitude ≈ 111 km
    dlon = (r * math.sin(angle)) / (111.0 * math.cos(math.radians(center_lat)))
    return round(center_lat + dlat, 5), round(center_lon + dlon, 5)


def generate_site(site_id="SN-CASA", center=(12.5833, -16.2833), n_hives=50,
                  n_crossroads=25, radius_km=6.0, seed=42):
    """Renvoie le site sous forme de dictionnaire {site_id, nodes, edges}."""
    rng = random.Random(seed)  # graine fixe : le même site à chaque exécution
    center_lat, center_lon = center

    base_id = f"COORD-{site_id}"
    nodes = [{"id": base_id, "type": "base", "lat": center_lat, "lon": center_lon}]
    crossroads = []
    for i in range(1, n_crossroads + 1):
        lat, lon = _random_point(rng, center_lat, center_lon, radius_km)
        nodes.append({"id": f"X-{i:02d}", "type": "carrefour", "lat": lat, "lon": lon})
        crossroads.append(nodes[-1])
    hives = []
    for i in range(1, n_hives + 1):
        lat, lon = _random_point(rng, center_lat, center_lon, radius_km)
        nodes.append({"id": f"{site_id}-{i:03d}", "type": "ruche", "lat": lat, "lon": lon})
        hives.append(nodes[-1])

    edges = []
    existing = set()

    def distance(a, b):
        return haversine_km(a["lat"], a["lon"], b["lat"], b["lon"])

    def nearest(node, candidates, k):
        others = [c for c in candidates if c["id"] != node["id"]]
        others.sort(key=lambda c: distance(node, c))
        return others[:k]

    def connect(a, b, road_type):
        pair = frozenset((a["id"], b["id"]))
        if pair in existing:
            return
        existing.add(pair)
        km = round(distance(a, b) * SINUOSITY, 3)
        minutes = round(km / ROAD_SPEEDS_KMH[road_type] * 60, 2)
        edges.append({"from": a["id"], "to": b["id"], "type": road_type,
                      "distance_km": km, "time_min": minutes})

    # 1. Réseau principal : chaque carrefour est relié à ses 3 plus proches voisins.
    for x in crossroads:
        for y in nearest(x, crossroads, 3):
            connect(x, y, "route" if rng.random() < 0.3 else "piste")

    # 2. On s'assure que tous les carrefours forment un seul bloc (connexe).
    _connect_components(crossroads, existing, connect, distance)

    # 3. La base du coordinateur rejoint les 2 carrefours les plus proches par la route.
    base = nodes[0]
    for x in nearest(base, crossroads, 2):
        connect(base, x, "route")

    # 4. Chaque ruche est desservie par le carrefour le plus proche, et une fois sur
    #    deux par un sentier vers la ruche voisine (chemins alternatifs, cycles).
    for h in hives:
        connect(h, nearest(h, crossroads, 1)[0], "piste" if rng.random() < 0.5 else "sentier")
        if rng.random() < 0.5:
            connect(h, nearest(h, hives, 1)[0], "sentier")

    return {"site_id": site_id, "nodes": nodes, "edges": edges}


def _connect_components(crossroads, existing, connect, distance):
    """Relie entre eux les morceaux isolés du réseau de carrefours."""
    while True:
        # Parcours en largeur (BFS) depuis le premier carrefour.
        ids = {x["id"] for x in crossroads}
        neighbors = {i: set() for i in ids}
        for pair in existing:
            a, b = tuple(pair)
            if a in ids and b in ids:
                neighbors[a].add(b)
                neighbors[b].add(a)
        start = crossroads[0]["id"]
        seen = {start}
        queue = [start]
        while queue:
            current = queue.pop()
            for n in neighbors[current]:
                if n not in seen:
                    seen.add(n)
                    queue.append(n)
        if len(seen) == len(crossroads):
            return
        # Sinon on relie le carrefour isolé le plus proche du bloc principal.
        inside = [x for x in crossroads if x["id"] in seen]
        outside = [x for x in crossroads if x["id"] not in seen]
        a, b = min(((a, b) for a in inside for b in outside), key=lambda p: distance(*p))
        connect(a, b, "piste")


def sparse_graph(n, avg_degree=4, seed=0):
    """Graphe aléatoire connexe et creux : |E| ≈ n * avg_degree / 2."""
    rng = random.Random(seed)
    graph = Graph()
    order = list(range(n))
    rng.shuffle(order)
    existing = set()
    # Une chaîne qui passe par tous les sommets garantit la connexité.
    for a, b in zip(order, order[1:]):
        graph.add_edge(a, b, rng.randint(1, 100))
        existing.add((min(a, b), max(a, b)))
    target_edges = min(n * avg_degree // 2, n * (n - 1) // 2)
    while len(existing) < target_edges:
        a, b = rng.randrange(n), rng.randrange(n)
        pair = (min(a, b), max(a, b))
        if a != b and pair not in existing:
            existing.add(pair)
            graph.add_edge(a, b, rng.randint(1, 100))
    if n == 1:
        graph.add_node(0)
    return graph


def dense_graph(n, density=0.5, seed=0):
    """Graphe aléatoire dense : chaque paire est reliée avec probabilité `density`."""
    rng = random.Random(seed)
    graph = Graph()
    for i in range(n):
        graph.add_node(i)
    for i in range(n):
        for j in range(i + 1, n):
            if j == i + 1 or rng.random() < density:  # j == i+1 : chaîne -> connexe
                graph.add_edge(i, j, rng.randint(1, 100))
    return graph


if __name__ == "__main__":
    site = generate_site()
    output = Path(__file__).resolve().parent.parent / "data" / "site_sn_casa.json"
    output.parent.mkdir(exist_ok=True)
    output.write_text(json.dumps(site, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"{len(site['nodes'])} sommets, {len(site['edges'])} arêtes -> {output}")
