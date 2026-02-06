from __future__ import annotations

from dataclasses import dataclass, field

from .types import ConversationNode


@dataclass
class ConversationTree:
    nodes: dict[str, ConversationNode] = field(default_factory=dict)
    children: dict[str | None, list[str]] = field(default_factory=lambda: {None: []})
    active_node_id: str | None = None

    def add_node(self, node: ConversationNode) -> None:
        self.nodes[node.id] = node
        self.children.setdefault(node.parent_id, []).append(node.id)
        self.children.setdefault(node.id, [])
        self.active_node_id = node.id

    def set_active(self, node_id: str) -> None:
        if node_id not in self.nodes:
            raise KeyError(f"Unknown node {node_id}")
        self.active_node_id = node_id

    def lineage(self, node_id: str | None = None) -> list[ConversationNode]:
        cursor = node_id or self.active_node_id
        ordered: list[ConversationNode] = []
        while cursor:
            n = self.nodes[cursor]
            ordered.append(n)
            cursor = n.parent_id
        return list(reversed(ordered))

    def to_dict(self) -> dict:
        return {
            "nodes": [n.to_dict() for n in self.nodes.values()],
            "active_node_id": self.active_node_id,
        }

    @staticmethod
    def from_dict(data: dict) -> "ConversationTree":
        tree = ConversationTree()
        tree.children = {None: []}
        for node_data in data.get("nodes", []):
            node = ConversationNode(**node_data)
            tree.add_node(node)
        if data.get("active_node_id"):
            tree.set_active(data["active_node_id"])
        return tree
