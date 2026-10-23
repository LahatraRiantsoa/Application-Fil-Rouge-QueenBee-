"""
Benchmark : Dijkstra avec tas binaire O((V+E) log V)  vs  version naïve O(V²).

Deux familles de graphes :
  - creux  (|E| ≈ 2|V|)    : ressemble à un vrai réseau de pistes
  - denses (|E| ≈ |V|²/4)  : chaque paire de sommets reliée avec probabilité 0,5

Lancer :  python -m benchmark.benchmark
Produit :  benchmark/results.csv  et  benchmark/benchmark.png
"""

import csv
import time
from pathlib import Path

from queenbee_routing.dijkstra import dijkstra
from queenbee_routing.dijkstra_naive import dijkstra_naive
from queenbee_routing.generator import dense_graph, sparse_graph

SPARSE_SIZES = [100, 250, 500, 1000, 2000, 4000]
DENSE_SIZES = [100, 250, 500, 1000, 1500]
REPEATS = 3
OUTPUT_DIR = Path(__file__).resolve().parent


def measure_ms(algorithm, graph, source):
    """Meilleur temps sur REPEATS exécutions (limite le bruit de la machine)."""
    best = float("inf")
    for _ in range(REPEATS):
        start = time.perf_counter()
        algorithm(graph, source)  # sans cible : on calcule tout l'arbre des chemins
        best = min(best, time.perf_counter() - start)
    return best * 1000


def run():
    rows = []
    for kind, sizes, build in [("creux", SPARSE_SIZES, sparse_graph),
                               ("dense", DENSE_SIZES, dense_graph)]:
        for n in sizes:
            graph = build(n)
            heap_ms = measure_ms(dijkstra, graph, 0)
            naive_ms = measure_ms(dijkstra_naive, graph, 0)
            row = {"type": kind, "V": n, "E": graph.edge_count(),
                   "tas_ms": round(heap_ms, 3), "naif_ms": round(naive_ms, 3),
                   "rapport_naif_sur_tas": round(naive_ms / heap_ms, 2)}
            rows.append(row)
            print(row)

    with open(OUTPUT_DIR / "results.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    plot(rows)


def plot(rows):
    import matplotlib
    matplotlib.use("Agg")  # génère l'image sans ouvrir de fenêtre
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    for ax, kind in zip(axes, ["creux", "dense"]):
        data = [r for r in rows if r["type"] == kind]
        v = [r["V"] for r in data]
        ax.plot(v, [r["tas_ms"] for r in data], "o-", label="Tas binaire  O((V+E) log V)")
        ax.plot(v, [r["naif_ms"] for r in data], "s--", label="Naïf  O(V²)")
        ax.set_title(f"Graphe {kind}")
        ax.set_xlabel("Nombre de sommets |V|")
        ax.set_ylabel("Temps (ms)")
        ax.grid(alpha=0.3)
        ax.legend()
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "benchmark.png", dpi=150)
    print(f"Graphique enregistré : {OUTPUT_DIR / 'benchmark.png'}")


if __name__ == "__main__":
    run()
