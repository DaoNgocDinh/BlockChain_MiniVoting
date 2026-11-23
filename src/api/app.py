"""MiniVoting Node HTTP API scaffold aligned with MiniVoting v1.

Provides process health, strict request boundary enforcement (body size limits,
Content-Encoding, Content-Type, duplicate JSON key rejection, standardized error
envelope, Cache-Control: no-store), and route skeletons for client and peer APIs.
Consensus and persistent ledger endpoints intentionally return 503
CONSENSUS_NOT_READY until W2/W3 integration.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from src.api.schemas import (
    DEFAULT_BLOCK_PAGE_LIMIT,
    MAX_BLOCK_PAGE_LIMIT,
    MAX_PROPOSAL_OR_FINALIZED_BODY_BYTES,
    MAX_TX_OR_VOTE_BODY_BYTES,
    MAX_UINT,
    AccountView,
    BlockPage,
    BlockRecord,
    ConsensusView,
    ErrorResponse,
    FinalizedBlock,
    HealthResponse,
    Metrics,
    NodeStatus,
    PeerReceipt,
    Proposal,
    RoundStatus,
    Transaction,
    TxLookup,
    TxSubmission,
    Vote,
)
from src.network.config import NodeConfig, load_cluster_config

POST_ROUTE_BODY_LIMITS: dict[str, int] = {
    "/transactions": MAX_TX_OR_VOTE_BODY_BYTES,
    "/peer/prepare": MAX_TX_OR_VOTE_BODY_BYTES,
    "/peer/commit": MAX_TX_OR_VOTE_BODY_BYTES,
    "/peer/propose": MAX_PROPOSAL_OR_FINALIZED_BODY_BYTES,
    "/peer/finalized": MAX_PROPOSAL_OR_FINALIZED_BODY_BYTES,
}


def _error_json_response(
    status_code: int,
    code: str,
    message: str,
    fields: list[dict[str, str]] | None = None,
) -> JSONResponse:
    detail: dict[str, Any] = {"code": code, "message": message}
    if fields is not None:
        detail["fields"] = fields
    return JSONResponse(
        status_code=status_code,
        content={"detail": detail},
        headers={"Cache-Control": "no-store"},
    )


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    obj: dict[str, Any] = {}
    for key, value in pairs:
        if key in obj:
            raise ValueError(f"Duplicate JSON key: {key}")
        obj[key] = value
    return obj


def _reject_non_finite_constant(token: str) -> Any:
    raise ValueError(f"Non-standard JSON constant not allowed: {token}")


class MiniVotingWireGuardMiddleware:
    """ASGI middleware enforcing MiniVoting v1 HTTP wire conventions.

    - Adds `Cache-Control: no-store` to dynamic API responses.
    - Rejects unsupported `Content-Encoding` (415) and non-JSON `Content-Type` (415).
    - Enforces per-route actual byte limits while streaming body chunks, even when
      `Content-Length` is omitted or chunked transfer encoding is used (413).
    - Rejects UTF-8 BOM, invalid UTF-8, duplicate JSON keys, and NaN/Infinity (400).
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        method: str = scope["method"].upper()
        path: str = scope["path"]
        headers = {k.lower(): v for k, v in scope.get("headers", ())}

        async def send_with_no_store(message: Message) -> None:
            if message["type"] == "http.response.start":
                raw_headers = list(message.get("headers", []))
                has_cc = any(k.lower() == b"cache-control" for k, _ in raw_headers)
                if not has_cc:
                    raw_headers.append((b"cache-control", b"no-store"))
                message = {**message, "headers": raw_headers}
            await send(message)

        if method == "POST" and path in POST_ROUTE_BODY_LIMITS:
            encoding_raw = headers.get(b"content-encoding")
            if encoding_raw is not None:
                encoding = encoding_raw.decode("latin-1").strip().lower()
                if encoding and encoding != "identity":
                    resp = _error_json_response(
                        status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                        "UNSUPPORTED_CONTENT_ENCODING",
                        "Only identity Content-Encoding is supported.",
                    )
                    await resp(scope, receive, send)
                    return

            content_type_raw = headers.get(b"content-type", b"").decode("latin-1")
            media_parts = [part.strip() for part in content_type_raw.split(";") if part.strip()]
            media_type = media_parts[0].lower() if media_parts else ""
            if media_type != "application/json":
                resp = _error_json_response(
                    status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                    "UNSUPPORTED_MEDIA_TYPE",
                    "Content-Type must be application/json.",
                )
                await resp(scope, receive, send)
                return

            for param in media_parts[1:]:
                if "=" in param:
                    pname, pval = [x.strip().lower() for x in param.split("=", 1)]
                    if pname == "charset" and pval.strip('"') != "utf-8":
                        resp = _error_json_response(
                            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                            "UNSUPPORTED_MEDIA_TYPE",
                            "Only UTF-8 charset is supported.",
                        )
                        await resp(scope, receive, send)
                        return

            limit = POST_ROUTE_BODY_LIMITS[path]
            chunks: list[bytes] = []
            total_bytes = 0
            while True:
                msg = await receive()
                if msg["type"] != "http.request":
                    break
                chunk = msg.get("body", b"")
                total_bytes += len(chunk)
                if total_bytes > limit:
                    resp = _error_json_response(
                        status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        "PAYLOAD_TOO_LARGE",
                        f"Request body exceeds route limit of {limit} bytes.",
                    )
                    await resp(scope, receive, send)
                    return
                if chunk:
                    chunks.append(chunk)
                if not msg.get("more_body", False):
                    break

            body_bytes = b"".join(chunks)
            if body_bytes.startswith(b"\xef\xbb\xbf"):
                resp = _error_json_response(
                    status.HTTP_400_BAD_REQUEST,
                    "MALFORMED_JSON",
                    "UTF-8 BOM is not allowed in JSON payloads.",
                )
                await resp(scope, receive, send)
                return

            try:
                text = body_bytes.decode("utf-8", errors="strict")
                json.loads(
                    text,
                    object_pairs_hook=_reject_duplicate_keys,
                    parse_constant=_reject_non_finite_constant,
                )
            except (UnicodeDecodeError, ValueError):
                resp = _error_json_response(
                    status.HTTP_400_BAD_REQUEST,
                    "MALFORMED_JSON",
                    "Request body must be valid UTF-8 JSON without duplicate keys or NaN/Infinity.",
                )
                await resp(scope, receive, send)
                return

            body_sent = False

            async def replay_receive() -> Message:
                nonlocal body_sent
                if not body_sent:
                    body_sent = True
                    return {"type": "http.request", "body": body_bytes, "more_body": False}
                return {"type": "http.request", "body": b"", "more_body": False}

            await self.app(scope, replay_receive, send_with_no_store)
            return

        await self.app(scope, receive, send_with_no_store)


def create_app(
    node_id: str | None = None,
    config_path: Path | str | None = None,
) -> FastAPI:
    """Create and configure a MiniVoting FastAPI instance for a specific validator node."""
    cluster_config = load_cluster_config(config_path)

    identity = node_id or os.environ.get("NODE_ID", "node1")
    if identity not in cluster_config.nodes:
        valid_nodes = ", ".join(sorted(cluster_config.nodes.keys()))
        raise ValueError(f"NODE_ID must be {valid_nodes}")

    node_config: NodeConfig = cluster_config.get_node(identity)

    app = FastAPI(
        title=f"MiniVoting Node - {identity}",
        version="0.1.0",
        description=(
            "Four-validator PBFT-inspired blockchain node API aligned with MiniVoting v1. "
            "Scaffold phase: Consensus and persistent ledger endpoints return 503 "
            "CONSENSUS_NOT_READY until W2/W3 integration."
        ),
    )
    app.add_middleware(MiniVotingWireGuardMiddleware)

    app.state.cluster_config = cluster_config
    app.state.node_config = node_config
    app.state.node_id = identity

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        _request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        fields: list[dict[str, str]] = []
        for err in exc.errors():
            loc = err.get("loc", ())
            if loc and loc[0] == "body":
                pointer = "/" + "/".join(str(part) for part in loc[1:])
            else:
                pointer = ".".join(str(part) for part in loc) or "request"
            fields.append({"path": pointer, "reason": str(err.get("msg", "Invalid value"))})
        return _error_json_response(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "INVALID_REQUEST",
            "Request validation failed.",
            fields=fields,
        )

    not_ready_exception = HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail={
            "code": "CONSENSUS_NOT_READY",
            "message": "Consensus and persistent ledger are not implemented yet.",
        },
    )

    # -------------------------------------------------------------------------
    # Core Observability Endpoints
    # -------------------------------------------------------------------------

    @app.get(
        "/health",
        response_model=HealthResponse,
        summary="Process Health Check",
        tags=["Observability"],
    )
    def health() -> HealthResponse:
        """Returns 200 OK when process is running.

        A responding process does NOT indicate consensus quorum or ledger synchronization.
        """
        return HealthResponse(
            status="ok",
            node_id=identity,  # type: ignore[arg-type]
            consensus_ready=False,
        )

    @app.get(
        "/status",
        response_model=NodeStatus,
        responses={503: {"model": ErrorResponse}},
        summary="Consensus & Ledger Status",
        tags=["Observability"],
    )
    def get_status() -> None:
        """Returns current consensus state, tip hash, and sync state."""
        raise not_ready_exception

    @app.get(
        "/metrics",
        response_model=Metrics,
        responses={503: {"model": ErrorResponse}},
        summary="Node Metrics",
        tags=["Observability"],
    )
    def get_metrics() -> None:
        """Returns per-process transaction and peer transport counters."""
        raise not_ready_exception

    # -------------------------------------------------------------------------
    # Client & Ledger Endpoints
    # -------------------------------------------------------------------------

    @app.post(
        "/transactions",
        response_model=TxSubmission,
        status_code=status.HTTP_202_ACCEPTED,
        responses={
            400: {"model": ErrorResponse},
            409: {"model": ErrorResponse},
            413: {"model": ErrorResponse},
            415: {"model": ErrorResponse},
            422: {"model": ErrorResponse},
            429: {"model": ErrorResponse},
            503: {"model": ErrorResponse},
        },
        summary="Submit Signed Transaction",
        tags=["Ledger"],
    )
    def submit_transaction(payload: Transaction) -> None:
        """Submit signed transaction to local mempool.

        202 Accepted means queued locally, NOT yet committed.
        """
        raise not_ready_exception

    @app.get(
        "/transactions/{tx_id}",
        response_model=TxLookup,
        responses={422: {"model": ErrorResponse}, 503: {"model": ErrorResponse}},
        summary="Query Transaction Status",
        tags=["Ledger"],
    )
    def get_transaction(tx_id: str) -> None:
        """Query local status (pending/proposed/committed/rejected/local-unknown)."""
        raise not_ready_exception

    @app.get(
        "/accounts/{address}",
        response_model=AccountView,
        responses={422: {"model": ErrorResponse}, 503: {"model": ErrorResponse}},
        summary="Query Committed Account State",
        tags=["Ledger"],
    )
    def get_account(address: str) -> None:
        """Query committed account balance and nonce snapshot."""
        raise not_ready_exception

    @app.get(
        "/blocks",
        response_model=BlockPage,
        responses={422: {"model": ErrorResponse}, 503: {"model": ErrorResponse}},
        summary="List Committed Blocks",
        tags=["Ledger"],
    )
    def list_blocks(
        from_height: int = Query(default=0, ge=0, le=MAX_UINT),
        limit: int = Query(default=DEFAULT_BLOCK_PAGE_LIMIT, ge=1, le=MAX_BLOCK_PAGE_LIMIT),
    ) -> None:
        """Paginated list of committed blocks in ascending height order."""
        raise not_ready_exception

    @app.get(
        "/blocks/{height}",
        response_model=BlockRecord,
        responses={
            404: {"model": ErrorResponse},
            422: {"model": ErrorResponse},
            503: {"model": ErrorResponse},
        },
        summary="Get Block Record by Height",
        tags=["Ledger"],
    )
    def get_block(height: int) -> None:
        """Return GenesisRecord at height 0 or FinalizedBlock at positive height."""
        raise not_ready_exception

    # -------------------------------------------------------------------------
    # Consensus Pull & Inspection Endpoints
    # Static routes MUST be registered BEFORE dynamic /consensus/{height}.
    # -------------------------------------------------------------------------

    @app.get(
        "/consensus/proposal",
        response_model=Proposal,
        responses={
            404: {"model": ErrorResponse},
            422: {"model": ErrorResponse},
            503: {"model": ErrorResponse},
        },
        summary="Fetch Stored Proposal for Height",
        tags=["Consensus"],
    )
    def get_consensus_proposal(height: int = Query(..., ge=1, le=MAX_UINT)) -> None:
        """Pull verified proposal stored for a round or committed block."""
        raise not_ready_exception

    @app.get(
        "/consensus/status",
        response_model=RoundStatus,
        responses={
            404: {"model": ErrorResponse},
            422: {"model": ErrorResponse},
            503: {"model": ErrorResponse},
        },
        summary="Probe Peer Round Status",
        tags=["Consensus"],
    )
    def get_consensus_status(height: int = Query(..., ge=1, le=MAX_UINT)) -> None:
        """Pull round status for slow probing when STALLED."""
        raise not_ready_exception

    @app.get(
        "/consensus/{height}",
        response_model=ConsensusView,
        responses={
            404: {"model": ErrorResponse},
            422: {"model": ErrorResponse},
            503: {"model": ErrorResponse},
        },
        summary="Inspect Consensus View for Height",
        tags=["Consensus"],
    )
    def get_consensus_view(height: int) -> None:
        """Return round status, proposal, voter IDs, certificate, and vote events."""
        raise not_ready_exception

    # -------------------------------------------------------------------------
    # Peer Wire Consensus Endpoints
    # -------------------------------------------------------------------------

    @app.post(
        "/peer/propose",
        response_model=PeerReceipt,
        status_code=status.HTTP_200_OK,
        responses={
            400: {"model": ErrorResponse},
            409: {"model": ErrorResponse},
            413: {"model": ErrorResponse},
            415: {"model": ErrorResponse},
            422: {"model": ErrorResponse},
            503: {"model": ErrorResponse},
        },
        summary="Receive Block Proposal from Leader",
        tags=["Peer Wire"],
    )
    def receive_propose(msg: Proposal) -> None:
        """Receive leader block proposal."""
        raise not_ready_exception

    @app.post(
        "/peer/prepare",
        response_model=PeerReceipt,
        status_code=status.HTTP_200_OK,
        responses={
            400: {"model": ErrorResponse},
            409: {"model": ErrorResponse},
            413: {"model": ErrorResponse},
            415: {"model": ErrorResponse},
            422: {"model": ErrorResponse},
            429: {"model": ErrorResponse},
            503: {"model": ErrorResponse},
        },
        summary="Receive PREPARE Vote",
        tags=["Peer Wire"],
    )
    def receive_prepare(msg: Vote) -> None:
        """Receive PREPARE vote from peer validator."""
        raise not_ready_exception

    @app.post(
        "/peer/commit",
        response_model=PeerReceipt,
        status_code=status.HTTP_200_OK,
        responses={
            400: {"model": ErrorResponse},
            409: {"model": ErrorResponse},
            413: {"model": ErrorResponse},
            415: {"model": ErrorResponse},
            422: {"model": ErrorResponse},
            429: {"model": ErrorResponse},
            503: {"model": ErrorResponse},
        },
        summary="Receive COMMIT Vote",
        tags=["Peer Wire"],
    )
    def receive_commit(msg: Vote) -> None:
        """Receive COMMIT vote from peer validator."""
        raise not_ready_exception

    @app.post(
        "/peer/finalized",
        response_model=PeerReceipt,
        status_code=status.HTTP_200_OK,
        responses={
            400: {"model": ErrorResponse},
            409: {"model": ErrorResponse},
            413: {"model": ErrorResponse},
            415: {"model": ErrorResponse},
            422: {"model": ErrorResponse},
            503: {"model": ErrorResponse},
        },
        summary="Receive Finalized Block & Commit Certificate",
        tags=["Peer Wire"],
    )
    def receive_finalized(msg: FinalizedBlock) -> None:
        """Receive finalized block with CommitCertificate for fast-path or sync."""
        raise not_ready_exception

    return app


app = create_app()
