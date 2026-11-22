"""Wire schemas and Pydantic models for MiniVoting API endpoints.

Aligned with TV2 consensus protocol specification (docs/protocol.md)
and TV3 API contract (docs/api-contract.md).
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

# -----------------------------------------------------------------------------
# System Constants & Limits (Bounded buffers and payloads)
# -----------------------------------------------------------------------------

MAX_TRANSACTION_PAYLOAD_BYTES: int = 64 * 1024  # 64 KB
MAX_REQUEST_BODY_BYTES: int = 1024 * 1024  # 1 MB
MAX_TRANSACTIONS_PER_BLOCK: int = 50
MAX_PENDING_MEMPOOL: int = 1000
MAX_BUFFERED_EARLY_VOTES: int = 100

PROPOSAL_TIMEOUT_SECONDS: float = 5.0
PREPARE_TIMEOUT_SECONDS: float = 2.0
COMMIT_TIMEOUT_SECONDS: float = 2.0
PEER_REQUEST_TIMEOUT_SECONDS: float = 2.0
MAX_FAST_RETRIES: int = 5
SLOW_PROBE_INTERVAL_SECONDS: float = 10.0


# -----------------------------------------------------------------------------
# Enums
# -----------------------------------------------------------------------------


class VotePhase(str, Enum):
    """Voting phases for the 3-phase consensus protocol."""

    PREPARE = "PREPARE"
    COMMIT = "COMMIT"


class ConsensusPhase(str, Enum):
    """Consensus state machine phases."""

    IDLE = "IDLE"
    WAIT_PROPOSAL = "WAIT_PROPOSAL"
    VALIDATING_PROPOSAL = "VALIDATING_PROPOSAL"
    PREPARING = "PREPARING"
    PREPARED = "PREPARED"
    COMMITTING = "COMMITTING"
    DECIDED = "DECIDED"
    LEADER_UNAVAILABLE = "LEADER_UNAVAILABLE"
    STALLED = "STALLED"
    SYNCING = "SYNCING"


class SyncState(str, Enum):
    """Ledger synchronization state."""

    IDLE = "IDLE"
    SYNCING = "SYNCING"
    CAUGHT_UP = "CAUGHT_UP"


class TransactionStatus(str, Enum):
    """Transaction lifecycle status.

    IMPORTANT: 'accepted' indicates accepted into mempool, NOT committed to ledger.
    """

    ACCEPTED = "accepted"
    PENDING = "pending"
    COMMITTED = "committed"
    REJECTED = "rejected"
    LOCAL_UNKNOWN = "local_unknown"


# -----------------------------------------------------------------------------
# Error Models
# -----------------------------------------------------------------------------


class ErrorDetail(BaseModel):
    """Standardized error structure."""

    code: str
    message: str
    details: dict[str, Any] | None = None


class ErrorResponse(BaseModel):
    """API error response wrapper."""

    detail: ErrorDetail


# -----------------------------------------------------------------------------
# Observability Models: Health & Status
# -----------------------------------------------------------------------------


class HealthResponse(BaseModel):
    """Process health check.

    Note: A responding process is NOT evidence of quorum or consensus readiness.
    """

    status: str = "ok"
    node_id: str
    consensus_ready: bool = False


class StatusResponse(BaseModel):
    """Consensus and ledger status for dashboard and monitoring."""

    node_id: str
    leader_id: str
    is_leader: bool
    chain_id: str
    committed_height: int
    target_height: int
    tip_hash: str
    phase: ConsensusPhase
    sync_state: SyncState
    is_locked: bool
    locked_block_hash: str | None = None
    is_stalled: bool
    peers_count: int
    peers_online: list[str] = Field(default_factory=list)


# -----------------------------------------------------------------------------
# Transaction Models
# -----------------------------------------------------------------------------


class TransactionPayload(BaseModel):
    """Signed transaction wire format."""

    chain_id: str = "minivoting-dev"
    sender: str = Field(min_length=1, max_length=128)
    recipient: str = Field(min_length=1, max_length=128)
    amount: int = Field(gt=0, description="Amount must be a strictly positive integer")
    nonce: int = Field(ge=0, description="Monotonically increasing sender nonce")
    signature: str = Field(min_length=64, description="Hex or base64 Ed25519 signature")


class TransactionReceipt(BaseModel):
    """Response returned upon POST /transactions or GET /transactions/{tx_id}."""

    tx_id: str
    status: TransactionStatus
    message: str
    block_height: int | None = None
    committed_at: str | None = None


# -----------------------------------------------------------------------------
# Block & Consensus Wire Models
# -----------------------------------------------------------------------------


class BlockHeader(BaseModel):
    """Block header fields verified in consensus and state machine."""

    height: int = Field(ge=0)
    prev_hash: str = Field(min_length=64, max_length=64)
    tx_list_hash: str = Field(min_length=64, max_length=64)
    state_hash: str = Field(min_length=64, max_length=64)
    proposer_id: str
    timestamp: int


class Block(BaseModel):
    """Full block containing header and list of transactions."""

    header: BlockHeader
    transactions: list[TransactionPayload] = Field(
        default_factory=list,
        max_length=MAX_TRANSACTIONS_PER_BLOCK,
    )


class VoteSignature(BaseModel):
    """Individual validator signature within a certificate."""

    sender_id: str
    signature: str = Field(min_length=64)


class CommitCertificate(BaseModel):
    """Proof of commit with at least 3/4 valid signatures."""

    height: int = Field(ge=0)
    view: int = 0
    block_hash: str = Field(min_length=64, max_length=64)
    signatures: list[VoteSignature] = Field(min_length=3, max_length=4)


class PreparedCertificate(BaseModel):
    """Proof of prepare with at least 3/4 valid signatures."""

    height: int = Field(ge=0)
    view: int = 0
    block_hash: str = Field(min_length=64, max_length=64)
    signatures: list[VoteSignature] = Field(min_length=3, max_length=4)


class VoteMessage(BaseModel):
    """Peer wire message for PREPARE and COMMIT phases."""

    protocol_version: str = "1.0"
    chain_id: str = "minivoting-dev"
    height: int = Field(ge=0)
    view: int = 0
    phase: VotePhase
    block_hash: str = Field(min_length=64, max_length=64)
    sender_id: str
    signature: str = Field(min_length=64)


class ProposalMessage(BaseModel):
    """Leader block proposal sent to followers."""

    protocol_version: str = "1.0"
    chain_id: str = "minivoting-dev"
    height: int = Field(ge=0)
    view: int = 0
    block: Block
    block_hash: str = Field(min_length=64, max_length=64)
    sender_id: str
    signature: str = Field(min_length=64)


class FinalizedBlockMessage(BaseModel):
    """Sync message carrying finalized block and its commit certificate."""

    protocol_version: str = "1.0"
    chain_id: str = "minivoting-dev"
    block: Block
    certificate: CommitCertificate


# -----------------------------------------------------------------------------
# Query & Observability Models
# -----------------------------------------------------------------------------


class AccountResponse(BaseModel):
    """Account state response."""

    address: str
    balance: int
    nonce: int
    committed_height: int


class BlockResponse(BaseModel):
    """Block explorer response."""

    height: int
    block_hash: str
    prev_hash: str
    state_hash: str
    tx_list_hash: str
    proposer_id: str
    timestamp: int
    tx_count: int
    transactions: list[TransactionPayload]
    certificate: CommitCertificate | None = None


class ConsensusStateResponse(BaseModel):
    """Detailed consensus snapshot for inspection and timeline visualization."""

    height: int
    view: int = 0
    phase: ConsensusPhase
    block_hash: str | None = None
    prepared_votes: list[VoteMessage] = Field(default_factory=list)
    commit_votes: list[VoteMessage] = Field(default_factory=list)
    is_locked: bool = False
    locked_block_hash: str | None = None
    is_stalled: bool = False


class EquivocationEvidence(BaseModel):
    """Byzantine equivocation evidence (two conflicting votes by same validator)."""

    height: int
    phase: VotePhase
    sender_id: str
    vote_a: VoteMessage
    vote_b: VoteMessage
    detected_at: str


class MetricsResponse(BaseModel):
    """Experiment and benchmark metrics."""

    node_id: str
    uptime_seconds: float
    committed_height: int
    total_transactions_committed: int
    total_votes_sent: int
    total_votes_received: int
    stalled_count: int
    equivocations_detected: int
