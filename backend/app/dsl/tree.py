from __future__ import annotations

from dataclasses import dataclass, field

from .parser import Parsed

ROOT_ID = "__root__"


@dataclass
class TreeNode:
    id: str
    kind: str  # 'root' | 'swimlane' | 'box' | 'shape' | 'group' | 'note' | 'edge'
    label: str = ""
    parent: str | None = None
    children: list[str] = field(default_factory=list)
    props: dict = field(default_factory=dict)


@dataclass
class Tree:
    nodes: dict[str, TreeNode] = field(default_factory=dict)
    root_id: str = ROOT_ID

    def ancestors(self, node_id: str) -> list[str]:
        out: list[str] = []
        cur = self.nodes.get(node_id)
        while cur and cur.parent:
            out.append(cur.parent)
            cur = self.nodes.get(cur.parent)
        return out

    def containers(self) -> list[TreeNode]:
        """Nodes that can own shapes as children (root + swimlanes + boxes)."""
        return [n for n in self.nodes.values() if n.kind in ("root", "swimlane", "box")]


def _swimlane_id(name: str) -> str:
    return f"swimlane:{name}"


def _box_id(label: str, swimlane: str | None) -> str:
    return f"box:{swimlane or ''}::{label}"


def build_tree(parsed: Parsed) -> Tree:
    tree = Tree()
    root = TreeNode(id=ROOT_ID, kind="root", label="(root)")
    tree.nodes[root.id] = root

    for sl in parsed.swimlanes:
        sid = _swimlane_id(sl.name)
        tree.nodes[sid] = TreeNode(
            id=sid,
            kind="swimlane",
            label=sl.name,
            parent=root.id,
            props={"name": sl.name},
        )
        root.children.append(sid)

    for b in parsed.boxes:
        parent_id = _swimlane_id(b.swimlane) if b.swimlane else root.id
        if parent_id not in tree.nodes:
            parent_id = root.id
        bid = _box_id(b.label, b.swimlane)
        tree.nodes[bid] = TreeNode(
            id=bid,
            kind="box",
            label=b.label,
            parent=parent_id,
            props={"label": b.label, "style": b.style, "swimlane": b.swimlane},
        )
        tree.nodes[parent_id].children.append(bid)

    for n in parsed.nodes:
        pid = root.id
        if n.box:
            candidate = _box_id(n.box, n.swimlane)
            if candidate in tree.nodes:
                pid = candidate
            elif n.swimlane and _swimlane_id(n.swimlane) in tree.nodes:
                pid = _swimlane_id(n.swimlane)
        elif n.swimlane and _swimlane_id(n.swimlane) in tree.nodes:
            pid = _swimlane_id(n.swimlane)

        node_props = {
            "shape": n.shape,
            "label": n.label,
            "step": n.step,
            "attrs": n.attrs,
            "style": n.style,
            "position": n.position,
        }
        tree.nodes[n.name] = TreeNode(
            id=n.name,
            kind="shape",
            label=n.name,
            parent=pid,
            props=node_props,
        )
        tree.nodes[pid].children.append(n.name)

    for g in parsed.groups:
        gid = f"group:{g.name}"
        tree.nodes[gid] = TreeNode(
            id=gid,
            kind="group",
            label=g.name,
            parent=root.id,
            props={"name": g.name, "members": list(g.members)},
        )
        root.children.append(gid)

    for i, note in enumerate(parsed.notes):
        nid = f"note:{i}"
        tree.nodes[nid] = TreeNode(
            id=nid,
            kind="note",
            label=note.text.split("\n")[0][:40] or "(note)",
            parent=root.id,
            props={"text": note.text, "target": note.target},
        )
        root.children.append(nid)

    for i, e in enumerate(parsed.edges):
        eid = f"edge:{i}"
        tree.nodes[eid] = TreeNode(
            id=eid,
            kind="edge",
            label=f"{e.source} → {e.target}",
            parent=root.id,
            props={
                "source": e.source,
                "target": e.target,
                "kind": e.kind,
                "label": e.label,
                "attrs": e.attrs,
            },
        )
        root.children.append(eid)

    return tree
