"""MiniVoting Node API application.

Provides process health, wire schema validation, and consensus/ledger
endpoints for the 4-validator permissioned blockchain cluster.
"""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, HTTPException, status

from src.api.schemas import (
    AccountResponse,
    BlockResponse,
    ConsensusStateResponse,
    ErrorResponse,
    FinalizedBlockMessage,
    HealthResponse,
    MetricsResponse,
    ProposalMessage,
    StatusResponse,
    TransactionPayload,
    TransactionReceipt,
    VoteMessage,
)
from src.network.config import NodeConfig, load_cluster_config


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
            "Four-validator PBFT-inspired blockchain node API. "
            "Scaffold phase: Consensus and persistent ledger endpoints return 503 "
            "CONSENSUS_NOT_READY until Week 3 full pipeline integration."
        ),
    )

    app.state.cluster_config = cluster_config
    app.state.node_config = node_config
    app.state.node_id = identity

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
            node_id=identity,
            consensus_ready=False,
        )

    @app.get(
        "/status",
        response_model=StatusResponse,
        responses={503: {"model": ErrorResponse}},
        summary="Consensus & Ledger Status",
        tags=["Observability"],
    )
    def get_status() -> None:
        """Returns current consensus state, tip hash, and sync status."""
        raise not_ready_exception

    @app.get(
        "/metrics",
        response_model=MetricsResponse,
        responses={503: {"model": ErrorResponse}},
        summary="Node Metrics",
        tags=["Observability"],
    )
    def get_metrics() -> None:
        """Returns operational metrics for benchmarking."""
        raise not_ready_exception

    # -------------------------------------------------------------------------
    # Client & Ledger Endpoints
    # -------------------------------------------------------------------------

    @app.post(
        "/transactions",
        response_model=TransactionReceipt,
        status_code=status.HTTP_202_ACCEPTED,
        responses={503: {"model": ErrorResponse}},
        summary="Submit Signed Transaction",
        tags=["Ledger"],
    )
    def submit_transaction(payload: TransactionPayload) -> None:
        """Submit signed transaction to local mempool.

        202 Accepted means queued for consensus, NOT yet committed.
        """
        raise not_ready_exception

    @app.get(
        "/transactions/{tx_id}",
        response_model=TransactionReceipt,
        responses={503: {"model": ErrorResponse}},
        summary="Query Transaction Status",
        tags=["Ledger"],
    )
    def get_transaction(tx_id: str) -> None:
        """Tra cứu trạng thái pending/committed/rejected của giao dịch."""
        raise not_ready_exception

    @app.get(
        "/accounts/{address}",
        response_model=AccountResponse,
        responses={503: {"model": ErrorResponse}},
        summary="Query Account Balance & Nonce",
        tags=["Ledger"],
    )
    def get_account(address: str) -> None:
        """Tra cứu số dư và nonce đã chốt của tài khoản."""
        raise not_ready_exception

    @app.get(
        "/blocks",
        response_model=list[BlockResponse],
        responses={503: {"model": ErrorResponse}},
        summary="List Committed Blocks",
        tags=["Ledger"],
    )
    def list_blocks(offset: int = 0, limit: int = 20) -> None:
        """Lấy danh sách các khối đã chốt có phân trang."""
        raise not_ready_exception

    @app.get(
        "/blocks/{height}",
        response_model=BlockResponse,
        responses={503: {"model": ErrorResponse}},
        summary="Get Block by Height",
        tags=["Ledger"],
    )
    def get_block(height: int) -> None:
        """Lấy thông tin khối và certificate chốt theo chiều cao."""
        raise not_ready_exception

    @app.get(
        "/consensus/{height}",
        response_model=ConsensusStateResponse,
        responses={503: {"model": ErrorResponse}},
        summary="Get Consensus State for Height",
        tags=["Consensus"],
    )
    def get_consensus_state(height: int) -> None:
        """Lấy trạng thái proposal, phiếu bầu và certificate tại chiều cao chỉ định."""
        raise not_ready_exception

    # -------------------------------------------------------------------------
    # Peer Wire Consensus Endpoints
    # -------------------------------------------------------------------------

    @app.post(
        "/peer/propose",
        response_model=dict[str, str],
        status_code=status.HTTP_202_ACCEPTED,
        responses={503: {"model": ErrorResponse}},
        summary="Receive Block Proposal from Leader",
        tags=["Peer Wire"],
    )
    def receive_propose(msg: ProposalMessage) -> None:
        """Follower receives block proposal from leader."""
        raise not_ready_exception

    @app.post(
        "/peer/prepare",
        response_model=dict[str, str],
        status_code=status.HTTP_202_ACCEPTED,
        responses={503: {"model": ErrorResponse}},
        summary="Receive PREPARE Vote",
        tags=["Peer Wire"],
    )
    def receive_prepare(msg: VoteMessage) -> None:
        """Validator receives PREPARE vote from peer."""
        raise not_ready_exception

    @app.post(
        "/peer/commit",
        response_model=dict[str, str],
        status_code=status.HTTP_202_ACCEPTED,
        responses={503: {"model": ErrorResponse}},
        summary="Receive COMMIT Vote",
        tags=["Peer Wire"],
    )
    def receive_commit(msg: VoteMessage) -> None:
        """Validator receives COMMIT vote from peer."""
        raise not_ready_exception

    @app.post(
        "/peer/finalized",
        response_model=dict[str, str],
        status_code=status.HTTP_200_OK,
        responses={503: {"model": ErrorResponse}},
        summary="Receive Finalized Block & Certificate",
        tags=["Peer Wire"],
    )
    def receive_finalized(msg: FinalizedBlockMessage) -> None:
        """Receive finalized block with commit certificate for synchronization."""
        raise not_ready_exception

    return app


app = create_app()
