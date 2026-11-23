"""Network, cluster, and runtime timeout configuration for MiniVoting nodes.

Provides topology validation, peer discovery, strict per-node storage/key
isolation, and validated runtime timeout overrides (env > config > defaults)
aligned with MiniVoting v1.
"""

from __future__ import annotations

import json
import math
import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DEFAULT_PEER_REQUEST_TIMEOUT_S: float = 1.0
DEFAULT_PROPOSAL_TIMEOUT_S: float = 5.0
DEFAULT_PREPARE_TIMEOUT_S: float = 2.0
DEFAULT_COMMIT_TIMEOUT_S: float = 2.0
DEFAULT_STALLED_PROBE_INTERVAL_S: float = 10.0
DEFAULT_STALLED_PROBE_JITTER_S: float = 2.0

RUNTIME_ENV_KEYS: dict[str, str] = {
    "peer_request_timeout_s": "MINIVOTING_PEER_REQUEST_TIMEOUT_S",
    "proposal_timeout_s": "MINIVOTING_PROPOSAL_TIMEOUT_S",
    "prepare_timeout_s": "MINIVOTING_PREPARE_TIMEOUT_S",
    "commit_timeout_s": "MINIVOTING_COMMIT_TIMEOUT_S",
    "stalled_probe_interval_s": "MINIVOTING_STALLED_PROBE_INTERVAL_S",
    "stalled_probe_jitter_s": "MINIVOTING_STALLED_PROBE_JITTER_S",
}


@dataclass(frozen=True)
class RuntimeTimeouts:
    """Validated operational timeouts for consensus timers and peer HTTP requests."""

    peer_request_timeout_s: float = DEFAULT_PEER_REQUEST_TIMEOUT_S
    proposal_timeout_s: float = DEFAULT_PROPOSAL_TIMEOUT_S
    prepare_timeout_s: float = DEFAULT_PREPARE_TIMEOUT_S
    commit_timeout_s: float = DEFAULT_COMMIT_TIMEOUT_S
    stalled_probe_interval_s: float = DEFAULT_STALLED_PROBE_INTERVAL_S
    stalled_probe_jitter_s: float = DEFAULT_STALLED_PROBE_JITTER_S

    def __post_init__(self) -> None:
        positive_fields = (
            "peer_request_timeout_s",
            "proposal_timeout_s",
            "prepare_timeout_s",
            "commit_timeout_s",
            "stalled_probe_interval_s",
        )
        for field_name in positive_fields:
            value = getattr(self, field_name)
            if isinstance(value, bool) or not isinstance(value, int | float):
                raise ValueError(f"Runtime timeout '{field_name}' must be a finite positive number")
            if not math.isfinite(value) or value <= 0:
                raise ValueError(f"Runtime timeout '{field_name}' must be > 0 and finite")

        jitter = self.stalled_probe_jitter_s
        if isinstance(jitter, bool) or not isinstance(jitter, int | float):
            raise ValueError("Runtime timeout 'stalled_probe_jitter_s' must be a finite number")
        if not math.isfinite(jitter) or jitter < 0:
            raise ValueError("Runtime timeout 'stalled_probe_jitter_s' must be >= 0 and finite")
        if jitter >= self.stalled_probe_interval_s:
            raise ValueError(
                "Runtime timeout 'stalled_probe_jitter_s' must be strictly less than "
                "'stalled_probe_interval_s'"
            )


def _parse_timeout_value(raw: Any, key_name: str) -> float:
    if isinstance(raw, bool):
        raise ValueError(f"Invalid boolean for runtime timeout '{key_name}'")
    if isinstance(raw, int | float):
        return float(raw)
    if isinstance(raw, str):
        text = raw.strip()
        if not text:
            raise ValueError(f"Empty value for runtime timeout '{key_name}'")
        try:
            return float(text)
        except ValueError as exc:
            raise ValueError(f"Invalid number for runtime timeout '{key_name}': {raw!r}") from exc
    raise ValueError(f"Unsupported type for runtime timeout '{key_name}': {type(raw).__name__}")


def load_runtime_timeouts(
    runtime_data: Mapping[str, Any] | None = None,
    environ: Mapping[str, str] | None = None,
) -> RuntimeTimeouts:
    """Resolve runtime timeouts with priority: environment > config > defaults."""
    env = os.environ if environ is None else environ
    cfg = runtime_data or {}

    if not isinstance(cfg, Mapping):
        raise ValueError("Config 'runtime' section must be a JSON object")

    unknown_keys = set(cfg.keys()) - set(RUNTIME_ENV_KEYS.keys())
    if unknown_keys:
        unknown_str = ", ".join(sorted(unknown_keys))
        raise ValueError(f"Unknown key(s) in config 'runtime' section: {unknown_str}")

    defaults = {
        "peer_request_timeout_s": DEFAULT_PEER_REQUEST_TIMEOUT_S,
        "proposal_timeout_s": DEFAULT_PROPOSAL_TIMEOUT_S,
        "prepare_timeout_s": DEFAULT_PREPARE_TIMEOUT_S,
        "commit_timeout_s": DEFAULT_COMMIT_TIMEOUT_S,
        "stalled_probe_interval_s": DEFAULT_STALLED_PROBE_INTERVAL_S,
        "stalled_probe_jitter_s": DEFAULT_STALLED_PROBE_JITTER_S,
    }

    resolved: dict[str, float] = {}
    for key, env_var in RUNTIME_ENV_KEYS.items():
        if env_var in env:
            resolved[key] = _parse_timeout_value(env[env_var], env_var)
        elif key in cfg:
            resolved[key] = _parse_timeout_value(cfg[key], key)
        else:
            resolved[key] = defaults[key]

    return RuntimeTimeouts(**resolved)


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
    """Cluster-wide topology, consensus, and runtime configuration."""

    chain_id: str
    leader_id: str
    quorum: int
    genesis_status: str
    nodes: dict[str, NodeConfig]
    runtime: RuntimeTimeouts = RuntimeTimeouts()

    def get_node(self, node_id: str) -> NodeConfig:
        if node_id not in self.nodes:
            valid_ids = ", ".join(sorted(self.nodes.keys()))
            raise ValueError(f"Unknown node ID '{node_id}'. Valid IDs: {valid_ids}")
        return self.nodes[node_id]

    def get_peers(self, node_id: str) -> list[NodeConfig]:
        """Return the other 3 validator nodes (peers) excluding self."""
        self.get_node(node_id)
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


def load_cluster_config(
    config_path: Path | str | None = None,
    environ: Mapping[str, str] | None = None,
) -> ClusterConfig:
    """Load and validate cluster topology and runtime timeouts from config/nodes.json."""
    if config_path is None:
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
        db_path = data_dir / "ledger.sqlite"

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

    runtime = load_runtime_timeouts(data.get("runtime"), environ=environ)

    return ClusterConfig(
        chain_id=chain_id,
        leader_id=leader_id,
        quorum=quorum,
        genesis_status=genesis_status,
        nodes=nodes_dict,
        runtime=runtime,
    )
