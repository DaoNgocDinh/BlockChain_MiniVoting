import pytest
from fastapi.testclient import TestClient

from src.api.app import create_app


@pytest.mark.parametrize("node_id", ["node1", "node2", "node3", "node4"])
def test_health_identifies_each_process_without_claiming_consensus(node_id):
    client = TestClient(create_app(node_id))
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "node_id": node_id,
        "consensus_ready": False,
    }


def test_status_does_not_fabricate_a_committed_ledger():
    response = TestClient(create_app("node1")).get("/status")
    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "CONSENSUS_NOT_READY"


def test_unknown_node_identity_is_rejected():
    with pytest.raises(ValueError, match="NODE_ID"):
        create_app("node5")
