"""Tests for cluster topology, configuration loading, and node isolation."""

import json
from pathlib import Path

import pytest

from src.network.config import NodeConfig, load_cluster_config


def test_load_cluster_config_success():
    config = load_cluster_config()
    assert config.chain_id == "minivoting-dev"
    assert config.leader_id == "node1"
    assert config.quorum == 3
    assert len(config.nodes) == 4

    # Verify all 4 nodes are properly loaded
    for nid in ["node1", "node2", "node3", "node4"]:
        assert nid in config.nodes
        node = config.get_node(nid)
        assert isinstance(node, NodeConfig)
        assert node.id == nid
        assert node.host == "127.0.0.1"
        assert node.port in {8001, 8002, 8003, 8004}


def test_all_nodes_have_strictly_isolated_directories_and_keys():
    config = load_cluster_config()
    ports = set()
    data_dirs = set()
    key_paths = set()
    db_paths = set()

    for node in config.nodes.values():
        assert node.port not in ports, f"Duplicate port {node.port}"
        assert node.data_dir not in data_dirs, f"Shared data_dir {node.data_dir}"
        assert node.key_path not in key_paths, f"Shared key_path {node.key_path}"
        assert node.db_path not in db_paths, f"Shared db_path {node.db_path}"

        ports.add(node.port)
        data_dirs.add(node.data_dir)
        key_paths.add(node.key_path)
        db_paths.add(node.db_path)

    assert len(ports) == 4
    assert len(data_dirs) == 4
    assert len(key_paths) == 4
    assert len(db_paths) == 4


def test_peer_discovery_returns_the_other_three_validators():
    config = load_cluster_config()

    for nid in ["node1", "node2", "node3", "node4"]:
        peers = config.get_peers(nid)
        peer_ids = {p.id for p in peers}
        assert len(peers) == 3
        assert nid not in peer_ids
        assert peer_ids == {"node1", "node2", "node3", "node4"} - {nid}


def test_leader_identification():
    config = load_cluster_config()
    assert config.is_leader("node1") is True
    assert config.is_leader("node2") is False
    assert config.is_leader("node3") is False
    assert config.is_leader("node4") is False


def test_unknown_node_query_raises_value_error():
    config = load_cluster_config()
    with pytest.raises(ValueError, match="Unknown node ID 'node99'"):
        config.get_node("node99")
    with pytest.raises(ValueError, match="Unknown node ID 'node99'"):
        config.get_peers("node99")


def test_config_validation_rejects_duplicate_ports(tmp_path: Path):
    invalid_data = {
        "chain_id": "test",
        "leader_id": "node1",
        "quorum": 3,
        "nodes": [
            {
                "id": "node1",
                "host": "127.0.0.1",
                "port": 8001,
                "data_dir": "data/1",
                "key_path": "keys/1.key",
            },
            {
                "id": "node2",
                "host": "127.0.0.1",
                "port": 8001,
                "data_dir": "data/2",
                "key_path": "keys/2.key",
            },
            {
                "id": "node3",
                "host": "127.0.0.1",
                "port": 8003,
                "data_dir": "data/3",
                "key_path": "keys/3.key",
            },
            {
                "id": "node4",
                "host": "127.0.0.1",
                "port": 8004,
                "data_dir": "data/4",
                "key_path": "keys/4.key",
            },
        ],
    }
    cfg_file = tmp_path / "nodes.json"
    cfg_file.write_text(json.dumps(invalid_data), encoding="utf-8")

    with pytest.raises(ValueError, match="Port conflict"):
        load_cluster_config(cfg_file)


def test_config_validation_rejects_non_4_nodes(tmp_path: Path):
    invalid_data = {
        "chain_id": "test",
        "leader_id": "node1",
        "quorum": 3,
        "nodes": [
            {
                "id": "node1",
                "host": "127.0.0.1",
                "port": 8001,
                "data_dir": "data/1",
                "key_path": "keys/1.key",
            },
            {
                "id": "node2",
                "host": "127.0.0.1",
                "port": 8002,
                "data_dir": "data/2",
                "key_path": "keys/2.key",
            },
            {
                "id": "node3",
                "host": "127.0.0.1",
                "port": 8003,
                "data_dir": "data/3",
                "key_path": "keys/3.key",
            },
        ],
    }
    cfg_file = tmp_path / "nodes.json"
    cfg_file.write_text(json.dumps(invalid_data), encoding="utf-8")

    with pytest.raises(ValueError, match="requires exactly 4 nodes"):
        load_cluster_config(cfg_file)
