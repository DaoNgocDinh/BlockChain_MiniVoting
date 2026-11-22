"""Tests for node API endpoints and scaffold behavior across all 4 nodes."""

import pytest
from fastapi.testclient import TestClient

from src.api.app import create_app


@pytest.fixture(params=["node1", "node2", "node3", "node4"])
def client(request):
    return TestClient(create_app(request.param))


def test_all_nodes_mount_health_correctly(client):
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["node_id"] in {"node1", "node2", "node3", "node4"}
    assert data["consensus_ready"] is False


def test_all_nodes_protect_against_unimplemented_consensus_endpoints(client):
    # Verify client and peer endpoints return 503 CONSENSUS_NOT_READY
    # rather than creating corrupted or fabricated ledger state
    endpoints = [
        ("GET", "/status"),
        ("GET", "/metrics"),
        ("GET", "/blocks"),
        ("GET", "/blocks/1"),
        ("GET", "/accounts/alice"),
        ("GET", "/consensus/1"),
        ("GET", "/transactions/tx_123"),
    ]

    for method, path in endpoints:
        if method == "GET":
            res = client.get(path)
        assert res.status_code == 503, f"{path} did not return 503"
        assert res.json()["detail"]["code"] == "CONSENSUS_NOT_READY"


def test_openapi_schema_generation():
    """Verify that OpenAPI documentation schema is complete and inspectable."""
    c = TestClient(create_app("node1"))
    res = c.get("/openapi.json")
    assert res.status_code == 200
    schema = res.json()

    assert "/health" in schema["paths"]
    assert "/status" in schema["paths"]
    assert "/transactions" in schema["paths"]
    assert "/peer/propose" in schema["paths"]
    assert "/peer/prepare" in schema["paths"]
    assert "/peer/commit" in schema["paths"]
    assert "/peer/finalized" in schema["paths"]
