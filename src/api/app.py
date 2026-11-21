"""Process health scaffold. Consensus and ledger endpoints belong to later issues."""

import os

from fastapi import FastAPI, HTTPException


def create_app(node_id: str | None = None) -> FastAPI:
    identity = node_id or os.environ.get("NODE_ID", "node1")
    if identity not in {"node1", "node2", "node3", "node4"}:
        raise ValueError("NODE_ID must be node1, node2, node3 or node4")

    app = FastAPI(title="MiniVoting Node", version="0.0.1")

    @app.get("/health")
    def health() -> dict[str, str | bool]:
        # A responding process is not evidence of a healthy consensus cluster.
        return {"status": "ok", "node_id": identity, "consensus_ready": False}

    @app.get("/status", status_code=503)
    def status() -> None:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "CONSENSUS_NOT_READY",
                "message": "Consensus and persistent ledger are not implemented yet.",
            },
        )

    return app


app = create_app()
