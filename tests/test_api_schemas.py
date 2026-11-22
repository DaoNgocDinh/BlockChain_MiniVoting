"""Unit tests for wire schemas, validation boundaries, and serialization."""

import pytest
from pydantic import ValidationError

from src.api.schemas import (
    Block,
    BlockHeader,
    CommitCertificate,
    ConsensusPhase,
    ErrorDetail,
    HealthResponse,
    ProposalMessage,
    StatusResponse,
    SyncState,
    TransactionPayload,
    VoteMessage,
    VotePhase,
    VoteSignature,
)


def test_health_response_schema():
    health = HealthResponse(status="ok", node_id="node1", consensus_ready=False)
    assert health.model_dump() == {
        "status": "ok",
        "node_id": "node1",
        "consensus_ready": False,
    }


def test_status_response_schema():
    status = StatusResponse(
        node_id="node1",
        leader_id="node1",
        is_leader=True,
        chain_id="minivoting-dev",
        committed_height=0,
        target_height=1,
        tip_hash="0" * 64,
        phase=ConsensusPhase.WAIT_PROPOSAL,
        sync_state=SyncState.IDLE,
        is_locked=False,
        locked_block_hash=None,
        is_stalled=False,
        peers_count=3,
        peers_online=["node2", "node3", "node4"],
    )
    dumped = status.model_dump()
    assert dumped["node_id"] == "node1"
    assert dumped["phase"] == "WAIT_PROPOSAL"
    assert dumped["peers_count"] == 3


def test_vote_message_validation():
    valid_vote = VoteMessage(
        protocol_version="1.0",
        chain_id="minivoting-dev",
        height=1,
        view=0,
        phase=VotePhase.PREPARE,
        block_hash="a" * 64,
        sender_id="node2",
        signature="s" * 64,
    )
    assert valid_vote.phase == VotePhase.PREPARE

    # Reject invalid hash length
    with pytest.raises(ValidationError):
        VoteMessage(
            height=1,
            phase=VotePhase.PREPARE,
            block_hash="short_hash",
            sender_id="node2",
            signature="s" * 64,
        )

    # Reject invalid phase
    with pytest.raises(ValidationError):
        VoteMessage(
            height=1,
            phase="INVALID_PHASE",  # type: ignore
            block_hash="a" * 64,
            sender_id="node2",
            signature="s" * 64,
        )


def test_commit_certificate_requires_at_least_3_signatures():
    sig1 = VoteSignature(sender_id="node1", signature="s" * 64)
    sig2 = VoteSignature(sender_id="node2", signature="s" * 64)
    sig3 = VoteSignature(sender_id="node3", signature="s" * 64)

    # 3 signatures -> Valid
    cert3 = CommitCertificate(
        height=1,
        view=0,
        block_hash="b" * 64,
        signatures=[sig1, sig2, sig3],
    )
    assert len(cert3.signatures) == 3

    # Less than 3 signatures -> Must fail validation
    with pytest.raises(ValidationError):
        CommitCertificate(
            height=1,
            view=0,
            block_hash="b" * 64,
            signatures=[sig1, sig2],
        )


def test_transaction_payload_validation():
    # Valid transaction
    tx = TransactionPayload(
        chain_id="minivoting-dev",
        sender="alice",
        recipient="bob",
        amount=100,
        nonce=0,
        signature="s" * 64,
    )
    assert tx.amount == 100

    # Reject amount <= 0
    with pytest.raises(ValidationError):
        TransactionPayload(
            sender="alice",
            recipient="bob",
            amount=0,
            nonce=0,
            signature="s" * 64,
        )

    with pytest.raises(ValidationError):
        TransactionPayload(
            sender="alice",
            recipient="bob",
            amount=-50,
            nonce=0,
            signature="s" * 64,
        )

    # Reject negative nonce
    with pytest.raises(ValidationError):
        TransactionPayload(
            sender="alice",
            recipient="bob",
            amount=10,
            nonce=-1,
            signature="s" * 64,
        )


def test_proposal_message_and_block():
    header = BlockHeader(
        height=1,
        prev_hash="0" * 64,
        tx_list_hash="1" * 64,
        state_hash="2" * 64,
        proposer_id="node1",
        timestamp=1700000000,
    )
    block = Block(header=header, transactions=[])
    prop = ProposalMessage(
        protocol_version="1.0",
        chain_id="minivoting-dev",
        height=1,
        view=0,
        block=block,
        block_hash="3" * 64,
        sender_id="node1",
        signature="s" * 64,
    )
    assert prop.sender_id == "node1"
    assert prop.block.header.height == 1


def test_error_detail_schema():
    err = ErrorDetail(
        code="CONSENSUS_NOT_READY",
        message="Consensus and persistent ledger are not implemented yet.",
        details={"node_id": "node1"},
    )
    assert err.code == "CONSENSUS_NOT_READY"
    assert err.details["node_id"] == "node1"
