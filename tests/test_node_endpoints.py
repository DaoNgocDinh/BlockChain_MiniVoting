"""Tests for MiniVoting v1 API routing, HTTP wire guards, and scaffold behavior."""

import json

import pytest
from fastapi.testclient import TestClient

from src.api.app import create_app
from src.api.schemas import MAX_PROPOSAL_OR_FINALIZED_BODY_BYTES, MAX_TX_OR_VOTE_BODY_BYTES


@pytest.fixture(params=["node1", "node2", "node3", "node4"])
def client(request):
    return TestClient(create_app(request.param))


def test_all_nodes_mount_health_correctly_with_no_store_header(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.headers.get("cache-control") == "no-store"
    data = res.json()
    assert data["status"] == "ok"
    assert data["node_id"] in {"node1", "node2", "node3", "node4"}
    assert data["consensus_ready"] is False


def test_all_nodes_protect_unimplemented_ledger_and_consensus_endpoints(client):
    endpoints = [
        "/status",
        "/metrics",
        "/blocks",
        "/blocks?from_height=0&limit=20",
        "/blocks/0",
        "/blocks/1",
        "/accounts/" + "a" * 64,
        "/transactions/" + "b" * 64,
        "/consensus/proposal?height=1",
        "/consensus/status?height=1",
        "/consensus/1",
    ]

    for path in endpoints:
        res = client.get(path)
        assert res.status_code == 503, f"{path} returned {res.status_code} instead of 503"
        assert res.headers.get("cache-control") == "no-store"
        assert res.json()["detail"]["code"] == "CONSENSUS_NOT_READY"


def test_static_consensus_routes_are_not_shadowed_by_dynamic_height_route():
    c = TestClient(create_app("node1"))
    # Missing required query param ?height=H hits the static route validation (422 INVALID_REQUEST)
    # rather than failing integer parsing for dynamic /consensus/{height}
    for static_path in ["/consensus/proposal", "/consensus/status"]:
        res = c.get(static_path)
        assert res.status_code == 422
        body = res.json()
        assert body["detail"]["code"] == "INVALID_REQUEST"
        assert any("height" in f["path"] for f in body["detail"]["fields"])

    # Valid query param height >= 1 reaches the static route handler (503 in scaffold)
    for static_path in ["/consensus/proposal?height=1", "/consensus/status?height=1"]:
        res = c.get(static_path)
        assert res.status_code == 503
        assert res.json()["detail"]["code"] == "CONSENSUS_NOT_READY"


def test_blocks_pagination_limit_enforces_v1_bounds():
    c = TestClient(create_app("node1"))
    for bad_query in ["limit=0", "limit=51", "from_height=-1"]:
        res = c.get(f"/blocks?{bad_query}")
        assert res.status_code == 422
        assert res.json()["detail"]["code"] == "INVALID_REQUEST"


def test_wire_guard_rejects_oversized_payloads_per_route():
    c = TestClient(create_app("node1"))

    # 4 KiB + 1 byte rejected on /transactions, /peer/prepare, /peer/commit
    oversized_small = b"{" + b" " * MAX_TX_OR_VOTE_BODY_BYTES + b"}"
    for route in ["/transactions", "/peer/prepare", "/peer/commit"]:
        res = c.post(
            route,
            content=oversized_small,
            headers={"Content-Type": "application/json"},
        )
        assert res.status_code == 413
        assert res.json()["detail"]["code"] == "PAYLOAD_TOO_LARGE"

    # 512 KiB + 1 byte rejected on /peer/propose, /peer/finalized
    oversized_large = b"{" + b" " * MAX_PROPOSAL_OR_FINALIZED_BODY_BYTES + b"}"
    for route in ["/peer/propose", "/peer/finalized"]:
        res = c.post(
            route,
            content=oversized_large,
            headers={"Content-Type": "application/json"},
        )
        assert res.status_code == 413
        assert res.json()["detail"]["code"] == "PAYLOAD_TOO_LARGE"


def test_wire_guard_rejects_bad_content_encoding_and_media_type():
    c = TestClient(create_app("node1"))

    res_enc = c.post(
        "/transactions",
        content=b"{}",
        headers={"Content-Type": "application/json", "Content-Encoding": "gzip"},
    )
    assert res_enc.status_code == 415
    assert res_enc.json()["detail"]["code"] == "UNSUPPORTED_CONTENT_ENCODING"

    res_type = c.post(
        "/transactions",
        content=b"{}",
        headers={"Content-Type": "text/plain"},
    )
    assert res_type.status_code == 415
    assert res_type.json()["detail"]["code"] == "UNSUPPORTED_MEDIA_TYPE"


def test_wire_guard_rejects_duplicate_json_keys_bom_and_nan():
    c = TestClient(create_app("node1"))
    headers = {"Content-Type": "application/json"}

    # Duplicate JSON keys
    res_dup = c.post("/peer/prepare", content=b'{"height":1,"height":2}', headers=headers)
    assert res_dup.status_code == 400
    assert res_dup.json()["detail"]["code"] == "MALFORMED_JSON"

    # UTF-8 BOM
    res_bom = c.post("/peer/prepare", content=b"\xef\xbb\xbf{}", headers=headers)
    assert res_bom.status_code == 400
    assert res_bom.json()["detail"]["code"] == "MALFORMED_JSON"

    # NaN constant
    res_nan = c.post("/peer/prepare", content=b'{"height":NaN}', headers=headers)
    assert res_nan.status_code == 400
    assert res_nan.json()["detail"]["code"] == "MALFORMED_JSON"


def test_validation_error_uses_standard_minivoting_v1_envelope():
    c = TestClient(create_app("node1"))
    res = c.post(
        "/peer/prepare",
        content=json.dumps({"protocol_version": 2}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    assert res.status_code == 422
    body = res.json()
    assert body["detail"]["code"] == "INVALID_REQUEST"
    assert isinstance(body["detail"]["fields"], list)
    assert len(body["detail"]["fields"]) > 0


def test_openapi_schema_includes_all_v1_routes():
    c = TestClient(create_app("node1"))
    res = c.get("/openapi.json")
    assert res.status_code == 200
    paths = res.json()["paths"]

    expected_paths = [
        "/health",
        "/status",
        "/metrics",
        "/transactions",
        "/transactions/{tx_id}",
        "/accounts/{address}",
        "/blocks",
        "/blocks/{height}",
        "/consensus/proposal",
        "/consensus/status",
        "/consensus/{height}",
        "/peer/propose",
        "/peer/prepare",
        "/peer/commit",
        "/peer/finalized",
    ]
    for path in expected_paths:
        assert path in paths, f"Missing OpenAPI route: {path}"
