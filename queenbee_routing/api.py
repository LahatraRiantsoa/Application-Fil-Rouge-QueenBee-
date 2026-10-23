"""
API REST du service de routage d'urgence QueenBee (cas d'usage UC-C01).

Lancer le serveur :
    uvicorn queenbee_routing.api:app --reload
Documentation interactive (Swagger) :
    http://127.0.0.1:8000/docs
"""

import os
import time
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .dijkstra import NoPathError, NodeNotFoundError, shortest_path
from .graph import Graph

DEFAULT_GRAPH_FILE = Path(__file__).resolve().parent.parent / "data" / "site_sn_casa.json"


# --- Modèles des données échangées (validés automatiquement par FastAPI) ----

class EmergencyPathRequest(BaseModel):
    start_id: str = Field(..., description="Point de départ du coordinateur",
                          examples=["COORD-SN-CASA"])
    hive_id: str = Field(..., description="Ruche en alerte critique",
                         examples=["SN-CASA-014"])


class EmergencyPathResponse(BaseModel):
    start_id: str
    hive_id: str
    total_cost_min: float = Field(..., description="Temps de trajet total (minutes)")
    path: list[str] = Field(..., description="Points de passage, dans l'ordre")
    steps: int = Field(..., description="Nombre de tronçons parcourus")
    computation_time_ms: float = Field(..., description="Temps de calcul de l'algorithme")


# --- Application -------------------------------------------------------------

def create_app(graph):
    """Construit l'application autour d'un graphe donné (pratique pour les tests)."""
    app = FastAPI(title="QueenBee - Routage d'urgence", version="1.0.0")

    @app.get("/health")
    def health():
        return {"status": "ok", "nodes": graph.node_count(), "edges": graph.edge_count()}

    @app.get("/api/v1/routing/nodes")
    def list_nodes(type: str | None = None):
        """Liste les sommets du site, filtrables par type (base, carrefour, ruche)."""
        return [
            {"id": node_id, **info}
            for node_id, info in graph.nodes.items()
            if type is None or info.get("type") == type
        ]

    @app.post("/api/v1/routing/emergency-path", response_model=EmergencyPathResponse)
    def emergency_path(request: EmergencyPathRequest):
        if request.hive_id in graph and graph.nodes[request.hive_id].get("type") != "ruche":
            raise HTTPException(422, f"{request.hive_id} n'est pas une ruche")

        # On ne chronomètre que l'algorithme, pas le réseau ni la sérialisation JSON.
        start = time.perf_counter()
        try:
            cost, path = shortest_path(graph, request.start_id, request.hive_id)
        except NodeNotFoundError as e:
            raise HTTPException(404, f"sommet inconnu : {e}")
        except NoPathError as e:
            raise HTTPException(422, str(e))
        elapsed_ms = (time.perf_counter() - start) * 1000

        return EmergencyPathResponse(
            start_id=request.start_id,
            hive_id=request.hive_id,
            total_cost_min=round(cost, 2),
            path=path,
            steps=len(path) - 1,
            computation_time_ms=round(elapsed_ms, 4),
        )

    return app


app = create_app(Graph.from_json_file(os.environ.get("QUEENBEE_GRAPH_FILE", DEFAULT_GRAPH_FILE)))
