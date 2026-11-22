"""Network and cluster configuration for MiniVoting nodes.

Provides topology validation, peer discovery, and strict file isolation
for the 4-validator permissioned blockchain network.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class NodeConfig:
    """Individual validator node configuration."""

    id: str
    host: str
    port: int
    data_dir: Path
    key_path: Path
    db_path: Path

    @property
    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}"


@dataclass(frozen=True)
class ClusterConfig:
    """Cluster-wide topology and consensus configuration."""

    chain_id: str
    leader_id: str
    quorum: int
    genesis_status: str
    nodes: dict[str, NodeConfig]

    def get_node(self, node_id: str) -> NodeConfig:
        if node_id not in self.nodes:
            valid_ids = ", ".join(sorted(self.nodes.keys()))
            raise ValueError(f"Unknown node ID '{node_id}'. Valid IDs: {valid_ids}")
        return self.nodes[node_id]

    def get_peers(self, node_id: str) -> list[NodeConfig]:
        """Return the other 3 validator nodes (peers) excluding self."""
        self.get_node(node_id)  # Validate node_id exists
        return [node for nid, node in self.nodes.items() if nid != node_id]

    def is_leader(self, node_id: str) -> bool:
        return node_id == self.leader_id

    def ensure_directories(self, project_root: Path | None = None) -> None:
        """Create isolated data directories and key directories for each node."""
        root = project_root or Path.cwd()
        for node in self.nodes.values():
            abs_data = (root / node.data_dir).resolve()
            abs_key_dir = (root / node.key_path).parent.resolve()
            abs_data.mkdir(parents=True, exist_ok=True)
            abs_key_dir.mkdir(parents=True, exist_ok=True)


def load_cluster_config(config_path: Path | str | None = None) -> ClusterConfig:
    """Load and validate cluster topology from config/nodes.json."""
    if config_path is None:
        # Default: search relative to project root
        candidates = [
            Path("config/nodes.json"),
            Path(__file__).resolve().parent.parent.parent / "config" / "nodes.json",
        ]
        resolved_path = next((p for p in candidates if p.is_file()), None)
        if resolved_path is None:
            raise FileNotFoundError("Could not find config/nodes.json")
    else:
        resolved_path = Path(config_path)
        if not resolved_path.is_file():
            raise FileNotFoundError(f"Configuration file not found: {resolved_path}")

    with open(resolved_path, encoding="utf-8") as f:
        data = json.load(f)

    chain_id = data.get("chain_id", "minivoting-dev")
    leader_id = data.get("leader_id", "node1")
    quorum = int(data.get("quorum", 3))
    genesis_status = data.get("genesis_status", "not-generated")
    raw_nodes = data.get("nodes", [])

    if len(raw_nodes) != 4:
        raise ValueError(f"MiniVoting cluster requires exactly 4 nodes, got {len(raw_nodes)}")

    nodes_dict: dict[str, NodeConfig] = {}
    seen_ports: set[int] = set()
    seen_data_dirs: set[Path] = set()
    seen_key_paths: set[Path] = set()

    for item in raw_nodes:
        nid = str(item["id"])
        host = str(item["host"])
        port = int(item["port"])
        data_dir = Path(item["data_dir"])
        key_path = Path(item["key_path"])
        db_path = data_dir / "ledger.db"

        if nid in nodes_dict:
            raise ValueError(f"Duplicate node ID detected: {nid}")
        if port in seen_ports:
            raise ValueError(f"Port conflict detected: port {port} assigned multiple times")
        if data_dir in seen_data_dirs:
            raise ValueError(f"Data directory conflict: {data_dir} assigned to multiple nodes")
        if key_path in seen_key_paths:
            raise ValueError(f"Key path conflict: {key_path} assigned to multiple nodes")

        seen_ports.add(port)
        seen_data_dirs.add(data_dir)
        seen_key_paths.add(key_path)

        nodes_dict[nid] = NodeConfig(
            id=nid,
            host=host,
            port=port,
            data_dir=data_dir,
            key_path=key_path,
            db_path=db_path,
        )

    if leader_id not in nodes_dict:
        raise ValueError(f"Configured leader_id '{leader_id}' is not among configured nodes")

    if quorum != 3:
        raise ValueError(f"MiniVoting protocol requires quorum = 3, got {quorum}")

    return ClusterConfig(
        chain_id=chain_id,
        leader_id=leader_id,
        quorum=quorum,
        genesis_status=genesis_status,
        nodes=nodes_dict,
    )
