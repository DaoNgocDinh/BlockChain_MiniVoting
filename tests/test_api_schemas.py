"""Unit tests for MiniVoting v1 wire schemas, strict validation, and API DTOs."""

import pytest
from pydantic import ValidationError

from src.api.schemas import (
    MAX_BLOCK_BYTES,
    MAX_BUFFERED_EARLY_VOTES,
    MAX_PENDING_MEMPOOL,
    MAX_PROPOSAL_OR_FINALIZED_BODY_BYTES,
    MAX_TRANSACTIONS_PER_BLOCK,
    MAX_TX_OR_VOTE_BODY_BYTES,
    AccountState,
    AccountView,
    Block,
    BlockHeader,
    BlockPage,
    BlockSummary,
    CommitCertificate,
    ConsensusView,
    ErrorDetail,
    ErrorField,
    FinalizedBlock,
    Genesis,
    GenesisRecord,
    HealthResponse,
    Metrics,
    NodeStatus,
    PeerCounters,
    PeerDirectionCounters,
    PeerReceipt,
    PreparedCertificate,
    Proposal,
    RoundStatus,
    Transaction,
    TxCounters,
    TxLookup,
    TxSubmission,
    ValidatorEntry,
    Vote,
    VoteEvent,
)

HASH_A = "a" * 64
HASH_B = "b" * 64
HASH_C = "c" * 64
HASH_ZERO = "0" * 64
SIG_A = "1" * 128
SIG_B = "2" * 128
SIG_C = "3" * 128


def _sample_transaction() -> dict:
    return {
        "protocol_version": 1,
        "chain_id": "minivoting-wire-test-1",
        "sender_public_key": "66c85538da226db0c531d36f75109bdf91a86802a0c4ec7d6b26dd1491fd5d21",
        "sender": "067bd8fae4ca0c3d10cc3502783ac051adb7e9f53ef17b4da7acd2430605c7d0",
        "recipient": "202a38ef89aef92d549d836af42d331a53ace4b2ae1b53a98cc44c18757f7151",
        "amount": 20,
        "nonce": 1,
        "tx_id": "3fe169de04efd7a429160d5609310850c2e650855056b51ed1e406424af529f3",
        "signature": (
            "de468e3b21d1d22f3b75873688388e8af11fb83cef62605d3be0086d151d752d"
            "f52f597cad2dfca025b0bb6bda39a537cf04c82fbe526e2785d18ae1d3eced06"
        ),
    }


def _sample_proposal() -> dict:
    return {
        "protocol_version": 1,
        "chain_id": "minivoting-wire-test-1",
        "height": 1,
        "view": 0,
        "phase": "PROPOSE",
        "block_hash": "4aa8473993e2afb11de15672b86762497cb304b49a07a691c9abfbfc69eed930",
        "sender_id": "node1",
        "signature": (
            "1bfc35796b206783fb5ce7a7e1fb466f460053ffed12de6fb6df848e6dbda053"
            "3bcf60de70ff94649d4ebce0f26c41524d203d042a3f478a633af26b4b20b107"
        ),
        "block": {
            "header": {
                "protocol_version": 1,
                "chain_id": "minivoting-wire-test-1",
                "height": 1,
                "prev_hash": "73f1c1865cb6265dceb6bf701eb7b160cbad18c352ecc4cc650752582c24d376",
                "proposer_id": "node1",
                "timestamp_ms": 1763784000000,
                "tx_list_hash": "a741b0e6987d821e3ea8c167b2c0c5796a9c87506bc928df19044fdbc852a770",
                "state_hash": "c35396645ebb9c37f809736d5c927efd376dff3c68870164477de66c462042a5",
            },
            "transactions": [_sample_transaction()],
            "block_hash": "4aa8473993e2afb11de15672b86762497cb304b49a07a691c9abfbfc69eed930",
        },
    }


def test_v1_constants_match_contract():
    assert MAX_TX_OR_VOTE_BODY_BYTES == 4 * 1024
    assert MAX_PROPOSAL_OR_FINALIZED_BODY_BYTES == 512 * 1024
    assert MAX_BLOCK_BYTES == 256 * 1024
    assert MAX_TRANSACTIONS_PER_BLOCK == 128
    assert MAX_PENDING_MEMPOOL == 1024
    assert MAX_BUFFERED_EARLY_VOTES == 50


def test_health_and_node_status_schemas():
    health = HealthResponse(status="ok", node_id="node1", consensus_ready=False)
    assert health.model_dump() == {
        "status": "ok",
        "node_id": "node1",
        "consensus_ready": False,
    }

    node_status = NodeStatus(
        protocol_version=1,
        chain_id="minivoting-dev",
        node_id="node1",
        leader_id="node1",
        committed_height=0,
        tip_hash=HASH_A,
        target_height=1,
        consensus_state="WAIT_PROPOSAL",
        phase="PROPOSE",
        sync_state="SYNCED",
        observed_at_ms=1763784000000,
    )
    assert node_status.phase == "PROPOSE"
    assert node_status.sync_state == "SYNCED"

    # Nullable phase allowed for SYNCING / INITIALIZING
    syncing_status = NodeStatus(
        protocol_version=1,
        chain_id="minivoting-dev",
        node_id="node2",
        leader_id="node1",
        committed_height=0,
        tip_hash=HASH_A,
        target_height=1,
        consensus_state="SYNCING",
        phase=None,
        sync_state="SYNCING",
        observed_at_ms=1763784000000,
    )
    assert syncing_status.phase is None


def test_genesis_record_validates_ordering_and_distinct_keys():
    genesis = Genesis(
        protocol_version=1,
        chain_id="minivoting-wire-test-1",
        height=0,
        prev_hash=HASH_ZERO,
        validators=[
            ValidatorEntry(node_id="node1", public_key="1" * 64),
            ValidatorEntry(node_id="node2", public_key="2" * 64),
            ValidatorEntry(node_id="node3", public_key="3" * 64),
            ValidatorEntry(node_id="node4", public_key="4" * 64),
        ],
        leader_id="node1",
        quorum=3,
        accounts=[AccountState(address=HASH_A, balance=100, nonce=0)],
        max_block_bytes=262144,
        max_transactions_per_block=128,
    )
    record = GenesisRecord(genesis=genesis, genesis_hash=HASH_B)
    assert record.genesis.height == 0

    # Wrong validator order rejected
    with pytest.raises(ValidationError, match="ordered strictly"):
        Genesis(
            protocol_version=1,
            chain_id="minivoting-wire-test-1",
            height=0,
            prev_hash=HASH_ZERO,
            validators=[
                ValidatorEntry(node_id="node2", public_key="2" * 64),
                ValidatorEntry(node_id="node1", public_key="1" * 64),
                ValidatorEntry(node_id="node3", public_key="3" * 64),
                ValidatorEntry(node_id="node4", public_key="4" * 64),
            ],
            leader_id="node1",
            quorum=3,
            accounts=[],
            max_block_bytes=262144,
            max_transactions_per_block=128,
        )


def test_transaction_strict_typing_rejects_bool_float_extra_and_bad_hex():
    tx = Transaction.model_validate(_sample_transaction())
    assert tx.amount == 20
    assert tx.nonce == 1

    # Reject bool masquerading as int (T03)
    bad_bool = {**_sample_transaction(), "amount": True}
    with pytest.raises(ValidationError):
        Transaction.model_validate(bad_bool)

    # Reject float amount (T03)
    bad_float = {**_sample_transaction(), "amount": 20.0}
    with pytest.raises(ValidationError):
        Transaction.model_validate(bad_float)

    # Reject amount = 0 or nonce = 0
    with pytest.raises(ValidationError):
        Transaction.model_validate({**_sample_transaction(), "amount": 0})
    with pytest.raises(ValidationError):
        Transaction.model_validate({**_sample_transaction(), "nonce": 0})

    # Reject extra unknown field
    with pytest.raises(ValidationError):
        Transaction.model_validate({**_sample_transaction(), "extra_field": 1})

    # Reject uppercase hex in hash/signature
    with pytest.raises(ValidationError):
        Transaction.model_validate({**_sample_transaction(), "tx_id": "A" * 64})
    with pytest.raises(ValidationError):
        Transaction.model_validate({**_sample_transaction(), "signature": "A" * 128})


def test_vote_and_certificates_with_map_signatures():
    vote = Vote(
        protocol_version=1,
        chain_id="minivoting-wire-test-1",
        height=1,
        view=0,
        phase="PREPARE",
        block_hash=HASH_A,
        sender_id="node2",
        signature=SIG_A,
    )
    assert vote.phase == "PREPARE"

    # PROPOSE is not valid for Vote
    with pytest.raises(ValidationError):
        Vote(
            protocol_version=1,
            chain_id="minivoting-wire-test-1",
            height=1,
            view=0,
            phase="PROPOSE",  # type: ignore[arg-type]
            block_hash=HASH_A,
            sender_id="node1",
            signature=SIG_A,
        )

    # PreparedCertificate & CommitCertificate require 3..4 distinct NodeId keys
    prep_cert = PreparedCertificate(
        protocol_version=1,
        chain_id="minivoting-wire-test-1",
        height=1,
        view=0,
        block_hash=HASH_A,
        signatures={"node1": SIG_A, "node2": SIG_B, "node3": SIG_C},
    )
    assert len(prep_cert.signatures) == 3

    with pytest.raises(ValidationError):
        CommitCertificate(
            protocol_version=1,
            chain_id="minivoting-wire-test-1",
            height=1,
            view=0,
            block_hash=HASH_A,
            signatures={"node1": SIG_A, "node2": SIG_B},
        )


def test_proposal_and_finalized_block_match_v1_fixture():
    prop = Proposal.model_validate(_sample_proposal())
    assert prop.phase == "PROPOSE"
    assert prop.block.header.height == 1

    # Block must contain at least 1 transaction
    with pytest.raises(ValidationError):
        Block(
            header=BlockHeader(
                protocol_version=1,
                chain_id="minivoting-dev",
                height=1,
                prev_hash=HASH_A,
                proposer_id="node1",
                timestamp_ms=1763784000000,
                tx_list_hash=HASH_B,
                state_hash=HASH_C,
            ),
            transactions=[],
            block_hash=HASH_A,
        )

    cert = CommitCertificate(
        protocol_version=1,
        chain_id="minivoting-wire-test-1",
        height=1,
        view=0,
        block_hash=prop.block_hash,
        signatures={"node1": SIG_A, "node2": SIG_B, "node3": SIG_C},
    )
    finalized = FinalizedBlock(proposal=prop, certificate=cert)
    assert finalized.certificate.block_hash == finalized.proposal.block_hash


def test_http_dtos_and_error_envelope():
    sub = TxSubmission(
        tx_id=HASH_A,
        admission="accepted",
        status="pending",
        observed_node_id="node2",
    )
    assert sub.admission == "accepted"

    lookup = TxLookup(
        tx_id=HASH_A,
        status="local-unknown",
        observed_node_id="node3",
        height=None,
        block_hash=None,
        reason=None,
    )
    assert lookup.status == "local-unknown"

    acct = AccountView(
        account=AccountState(address=HASH_A, balance=100, nonce=1),
        committed_height=1,
        tip_hash=HASH_B,
    )
    assert acct.account.balance == 100

    page = BlockPage(
        items=[
            BlockSummary(height=0, block_hash=HASH_A, timestamp_ms=None, transaction_count=0),
            BlockSummary(
                height=1, block_hash=HASH_B, timestamp_ms=1763784000000, transaction_count=1
            ),
        ],
        next_from_height=None,
        committed_height=1,
    )
    assert len(page.items) == 2

    round_status = RoundStatus(
        node_id="node1",
        height=1,
        committed_height=0,
        target_height=1,
        consensus_state="COMMITTING",
        phase="COMMIT",
        proposal_hash=HASH_A,
        prepare_count=3,
        commit_count=2,
        is_locked=True,
        observed_at_ms=1763784000000,
    )
    view = ConsensusView(
        round=round_status,
        proposal=None,
        prepare_voter_ids=["node1", "node2", "node3"],
        commit_voter_ids=["node1", "node2"],
        certificate=None,
        events=[
            VoteEvent(
                seq=1,
                observed_at_ms=1763784000001,
                peer_id="node3",
                sender_id="node4",
                phase="COMMIT",
                block_hash=HASH_A,
                outcome="invalid",
                reason="INVALID_SIGNATURE",
            )
        ],
    )
    assert view.events[0].outcome == "invalid"

    zero = PeerDirectionCounters(sent=0, received=0, retry_sent=0, sent_bytes=0, received_bytes=0)
    metrics = Metrics(
        node_id="node1",
        process_started_at_ms=1763784000000,
        observed_at_ms=1763784001000,
        transactions=TxCounters(submitted=1, admitted=1, rejected=0, committed=0),
        peer=PeerCounters(propose=zero, prepare=zero, commit=zero, finalized=zero),
    )
    assert metrics.transactions.submitted == 1

    receipt = PeerReceipt(node_id="node2", height=1, outcome="sync-required")
    assert receipt.outcome == "sync-required"

    err = ErrorDetail(
        code="INVALID_REQUEST",
        message="Validation failed",
        fields=[ErrorField(path="/amount", reason="must be positive")],
    )
    assert err.fields is not None and err.fields[0].path == "/amount"
