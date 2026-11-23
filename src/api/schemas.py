"""Wire schemas and HTTP API DTOs for MiniVoting v1.

Aligned 100% with the MiniVoting v1 communication contract (PR #27):
- docs/wire-models.md
- docs/api-contract.md
- docs/module-interfaces.md
"""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StrictInt, field_validator

# -----------------------------------------------------------------------------
# MiniVoting v1 Constants, Limits & Default Timeouts
# -----------------------------------------------------------------------------

PROTOCOL_VERSION: int = 1
VIEW_FIXED: int = 0
QUORUM_FIXED: int = 3
MAX_UINT: int = (1 << 53) - 1  # 9007199254740991 (JavaScript safe integer)

KIB: int = 1024
MAX_TX_OR_VOTE_BODY_BYTES: int = 4 * KIB  # 4 KiB
MAX_PROPOSAL_OR_FINALIZED_BODY_BYTES: int = 512 * KIB  # 512 KiB
MAX_BLOCK_BYTES: int = 256 * KIB  # 262,144 bytes
MAX_TRANSACTIONS_PER_BLOCK: int = 128

MAX_PENDING_MEMPOOL: int = 1024
MAX_BUFFERED_EARLY_VOTES: int = 50
MAX_VOTE_EVENTS_IN_MEMORY: int = 100
TX_MEMPOOL_TTL_SECONDS: int = 300

DEFAULT_BLOCK_PAGE_LIMIT: int = 20
MAX_BLOCK_PAGE_LIMIT: int = 50

PEER_REQUEST_TIMEOUT_SECONDS: float = 1.0
PROPOSAL_TIMEOUT_SECONDS: float = 5.0
PREPARE_TIMEOUT_SECONDS: float = 2.0
COMMIT_TIMEOUT_SECONDS: float = 2.0
STALLED_PROBE_INTERVAL_SECONDS: float = 10.0
STALLED_PROBE_JITTER_SECONDS: float = 2.0
MAX_FAST_RETRIES: int = 5


# -----------------------------------------------------------------------------
# Constrained Primitive Types (wire-models.md §1)
# -----------------------------------------------------------------------------

Version = Literal[1]
View = Literal[0]
Quorum = Literal[3]
NodeId = Literal["node1", "node2", "node3", "node4"]

ChainId = Annotated[str, Field(pattern=r"^[a-z0-9][a-z0-9_-]{0,63}$")]
Hash32 = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
Address = Hash32
PublicKey32 = Hash32
Signature64 = Annotated[str, Field(pattern=r"^[0-9a-f]{128}$")]

UInt = Annotated[StrictInt, Field(ge=0, le=MAX_UINT)]
PositiveUInt = Annotated[StrictInt, Field(ge=1, le=MAX_UINT)]

Phase = Literal["PROPOSE", "PREPARE", "COMMIT"]
VotePhase = Literal["PREPARE", "COMMIT"]
ConsensusState = Literal[
    "INITIALIZING",
    "WAIT_PROPOSAL",
    "VALIDATING_PROPOSAL",
    "PREPARING",
    "PREPARED",
    "COMMITTING",
    "DECIDED",
    "LEADER_UNAVAILABLE",
    "STALLED",
    "SYNCING",
]
SyncState = Literal["SYNCED", "SYNCING"]
TxStatus = Literal["pending", "proposed", "committed", "rejected", "local-unknown"]
TxAdmission = Literal["accepted", "already-known"]
TxSubmissionStatus = Literal["pending", "proposed", "committed"]
PeerOutcome = Literal[
    "accepted",
    "duplicate",
    "buffered",
    "ignored-stale",
    "applied",
    "sync-required",
]
VoteEventOutcome = Literal["valid", "invalid", "duplicate", "buffered", "equivocation"]


class StrictWireModel(BaseModel):
    """Base model enforcing MiniVoting v1 strict typing and rejecting extra fields."""

    model_config = ConfigDict(extra="forbid", strict=True)


# -----------------------------------------------------------------------------
# Standard Error Envelope (api-contract.md §1)
# -----------------------------------------------------------------------------


class ErrorField(BaseModel):
    """Per-field validation error descriptor."""

    path: str
    reason: str


class ErrorDetail(BaseModel):
    """Machine-readable error payload inside standard HTTP error envelope."""

    code: str
    message: str
    fields: list[ErrorField] | None = None


class ErrorResponse(BaseModel):
    """Standardized MiniVoting v1 API error wrapper."""

    detail: ErrorDetail


# -----------------------------------------------------------------------------
# Core Wire Models (wire-models.md §2–§4)
# -----------------------------------------------------------------------------


class ValidatorEntry(StrictWireModel):
    """Genesis validator registry item."""

    node_id: NodeId
    public_key: PublicKey32


class AccountState(StrictWireModel):
    """Committed account balance and nonce."""

    address: Address
    balance: UInt
    nonce: UInt


class Genesis(StrictWireModel):
    """Public genesis configuration committed at height 0."""

    protocol_version: Version
    chain_id: ChainId
    height: Literal[0]
    prev_hash: Hash32
    validators: list[ValidatorEntry] = Field(min_length=4, max_length=4)
    leader_id: NodeId
    quorum: Quorum
    accounts: list[AccountState]
    max_block_bytes: PositiveUInt = Field(le=MAX_BLOCK_BYTES)
    max_transactions_per_block: PositiveUInt = Field(le=MAX_TRANSACTIONS_PER_BLOCK)

    @field_validator("validators")
    @classmethod
    def validate_validators_order_and_uniqueness(
        cls, value: list[ValidatorEntry]
    ) -> list[ValidatorEntry]:
        expected_order = ["node1", "node2", "node3", "node4"]
        if [v.node_id for v in value] != expected_order:
            raise ValueError("validators must be ordered strictly as node1, node2, node3, node4")
        if len({v.public_key for v in value}) != 4:
            raise ValueError("validator public keys must be distinct")
        return value


class GenesisRecord(StrictWireModel):
    """Genesis paired with its canonical SHA-256 hash."""

    genesis: Genesis
    genesis_hash: Hash32


class Transaction(StrictWireModel):
    """Signed transfer transaction on the wire."""

    protocol_version: Version
    chain_id: ChainId
    sender_public_key: PublicKey32
    sender: Address
    recipient: Address
    amount: PositiveUInt
    nonce: PositiveUInt
    tx_id: Hash32
    signature: Signature64


class BlockHeader(StrictWireModel):
    """Block header fields hashed into block_hash."""

    protocol_version: Version
    chain_id: ChainId
    height: PositiveUInt
    prev_hash: Hash32
    proposer_id: NodeId
    timestamp_ms: UInt
    tx_list_hash: Hash32
    state_hash: Hash32


class Block(StrictWireModel):
    """Block body with header, non-empty transaction list, and block_hash."""

    header: BlockHeader
    transactions: list[Transaction] = Field(min_length=1, max_length=MAX_TRANSACTIONS_PER_BLOCK)
    block_hash: Hash32


class SignedContext(StrictWireModel):
    """Exact 7-field signing context shared by PROPOSE, PREPARE, and COMMIT."""

    protocol_version: Version
    chain_id: ChainId
    height: PositiveUInt
    view: View
    phase: Phase
    block_hash: Hash32
    sender_id: NodeId


class Proposal(StrictWireModel):
    """Leader proposal envelope: 7 SignedContext fields + signature + attached block."""

    protocol_version: Version
    chain_id: ChainId
    height: PositiveUInt
    view: View
    phase: Literal["PROPOSE"]
    block_hash: Hash32
    sender_id: NodeId
    signature: Signature64
    block: Block


class Vote(StrictWireModel):
    """Peer wire message for PREPARE and COMMIT voting phases."""

    protocol_version: Version
    chain_id: ChainId
    height: PositiveUInt
    view: View
    phase: VotePhase
    block_hash: Hash32
    sender_id: NodeId
    signature: Signature64


class _BaseCertificate(StrictWireModel):
    protocol_version: Version
    chain_id: ChainId
    height: PositiveUInt
    view: View
    block_hash: Hash32
    signatures: dict[NodeId, Signature64] = Field(min_length=3, max_length=4)


class PreparedCertificate(_BaseCertificate):
    """Proof of PREPARE quorum with 3 or 4 distinct validator signatures."""


class CommitCertificate(_BaseCertificate):
    """Proof of COMMIT finality with 3 or 4 distinct validator signatures."""


class FinalizedBlock(StrictWireModel):
    """Finalized block payload carrying leader proposal and commit certificate."""

    proposal: Proposal
    certificate: CommitCertificate


# -----------------------------------------------------------------------------
# HTTP API Response DTOs (api-contract.md §2–§3)
# -----------------------------------------------------------------------------


class HealthResponse(StrictWireModel):
    """Process health response. Responding OK does not imply quorum or sync."""

    status: Literal["ok"] = "ok"
    node_id: NodeId
    consensus_ready: bool = False


class NodeStatus(StrictWireModel):
    """Node consensus and synchronization snapshot returned by GET /status."""

    protocol_version: Version
    chain_id: ChainId
    node_id: NodeId
    leader_id: NodeId
    committed_height: UInt
    tip_hash: Hash32
    target_height: PositiveUInt
    consensus_state: ConsensusState
    phase: Phase | None
    sync_state: SyncState
    observed_at_ms: UInt


class TxSubmission(StrictWireModel):
    """Response returned by POST /transactions. 202 accepted does not imply committed."""

    tx_id: Hash32
    admission: TxAdmission
    status: TxSubmissionStatus
    observed_node_id: NodeId


class TxLookup(StrictWireModel):
    """Per-node transaction status returned by GET /transactions/{tx_id}."""

    tx_id: Hash32
    status: TxStatus
    observed_node_id: NodeId
    height: PositiveUInt | None
    block_hash: Hash32 | None
    reason: str | None


class AccountView(StrictWireModel):
    """Committed account state snapshot returned by GET /accounts/{address}."""

    account: AccountState
    committed_height: UInt
    tip_hash: Hash32


class BlockSummary(StrictWireModel):
    """Summary entry in paginated GET /blocks response."""

    height: UInt
    block_hash: Hash32
    timestamp_ms: UInt | None
    transaction_count: UInt


class BlockPage(StrictWireModel):
    """Paginated committed block list returned by GET /blocks."""

    items: list[BlockSummary]
    next_from_height: PositiveUInt | None
    committed_height: UInt


BlockRecord = GenesisRecord | FinalizedBlock


class RoundStatus(StrictWireModel):
    """Round observation returned by GET /consensus/status?height=H and ConsensusView."""

    node_id: NodeId
    height: PositiveUInt
    committed_height: UInt
    target_height: PositiveUInt
    consensus_state: ConsensusState
    phase: Phase | None
    proposal_hash: Hash32 | None
    prepare_count: UInt
    commit_count: UInt
    is_locked: bool
    observed_at_ms: UInt


class VoteEvent(StrictWireModel):
    """Timeline event observed at a validator node."""

    seq: UInt
    observed_at_ms: UInt
    peer_id: NodeId | None
    sender_id: NodeId | None
    phase: VotePhase
    block_hash: Hash32 | None
    outcome: VoteEventOutcome
    reason: str | None


class ConsensusView(StrictWireModel):
    """Detailed consensus inspection returned by GET /consensus/{height}."""

    round: RoundStatus
    proposal: Proposal | None
    prepare_voter_ids: list[NodeId]
    commit_voter_ids: list[NodeId]
    certificate: CommitCertificate | None
    events: list[VoteEvent]


class TxCounters(StrictWireModel):
    """Per-process transaction counters."""

    submitted: UInt
    admitted: UInt
    rejected: UInt
    committed: UInt


class PeerDirectionCounters(StrictWireModel):
    """Per-message-type peer transport counters."""

    sent: UInt
    received: UInt
    retry_sent: UInt
    sent_bytes: UInt
    received_bytes: UInt


class PeerCounters(StrictWireModel):
    """Transport counters grouped by consensus message type."""

    propose: PeerDirectionCounters
    prepare: PeerDirectionCounters
    commit: PeerDirectionCounters
    finalized: PeerDirectionCounters


class Metrics(StrictWireModel):
    """Process metrics returned by GET /metrics."""

    node_id: NodeId
    process_started_at_ms: UInt
    observed_at_ms: UInt
    transactions: TxCounters
    peer: PeerCounters


class PeerReceipt(StrictWireModel):
    """Peer endpoint acknowledgment returned by /peer/* routes."""

    node_id: NodeId
    height: PositiveUInt
    outcome: PeerOutcome
