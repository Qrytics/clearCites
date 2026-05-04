import type { Edge, Node } from "reactflow";
import dagre from "@dagrejs/dagre";

function nodeBox(node: Node): { w: number; h: number } {
  const st = node.style as { width?: number | string; height?: number | string } | undefined;
  const w =
    typeof st?.width === "number"
      ? st.width
      : typeof st?.width === "string"
        ? parseInt(st.width, 10) || 120
        : 120;
  const h =
    typeof st?.height === "number"
      ? st.height
      : typeof st?.height === "string"
        ? parseInt(st.height, 10) || 48
        : 48;
  return { w: Math.max(w, 40), h: Math.max(h, 32) };
}

/** Assign top-left positions using Dagre (layered LR layout). */
export function layoutWithDagre(nodes: Node[], edges: Edge[]): Node[] {
  if (nodes.length === 0) return [];
  const g = new dagre.graphlib.Graph();
  g.setDefaultEdgeLabel(() => ({}));
  g.setGraph({
    rankdir: "LR",
    ranksep: 72,
    nodesep: 48,
    marginx: 24,
    marginy: 24,
  });

  nodes.forEach((node) => {
    const { w, h } = nodeBox(node);
    g.setNode(node.id, { width: w, height: h });
  });
  edges.forEach((e) => {
    if (g.hasNode(e.source) && g.hasNode(e.target)) {
      g.setEdge(e.source, e.target);
    }
  });
  dagre.layout(g);

  return nodes.map((node) => {
    const pos = g.node(node.id);
    const { w, h } = nodeBox(node);
    if (!pos || typeof pos.x !== "number") {
      return { ...node, position: { x: 0, y: 0 } };
    }
    return {
      ...node,
      position: { x: pos.x - w / 2, y: pos.y - h / 2 },
    };
  });
}
