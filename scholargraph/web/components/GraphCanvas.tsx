import React, { useCallback, useEffect, useState } from "react";
import ReactFlow, {
  addEdge,
  Background,
  Connection,
  Controls,
  Edge,
  MiniMap,
  Node,
  useEdgesState,
  useNodesState,
} from "reactflow";
import "reactflow/dist/style.css";

import PaperDetail from "./PaperDetail";
import { useGraphData } from "../hooks/useGraphData";

interface PaperData {
  doi: string;
  title: string;
  year?: number;
  cited_by_count?: number;
  impact_score?: number;
  funding_source?: string;
  abstract?: string;
  authors?: string[];
  keywords?: string[];
  funders?: string[];
  plain_summary?: string;
}

interface GraphNode extends Node {
  /** API may attach kind: paper | author | keyword; papers include doi/title fields. */
  data: (Partial<PaperData> & { label: string; kind?: string }) | Record<string, unknown>;
}

interface Props {
  seedDoi: string;
  depth?: number;
  /** Comma list passed to GET /graph (e.g. citations,authors,coauthors,keywords). */
  expand?: string;
}

type NodeKind = "paper" | "author" | "keyword" | undefined;

/** Visual style by node kind; papers scale with impact_score (0–1). */
function nodeStyle(data: Record<string, unknown> | undefined): React.CSSProperties {
  const kind = data?.kind as NodeKind;
  if (kind === "author") {
    return {
      width: 120,
      minHeight: 36,
      borderRadius: 8,
      background: "rgba(245, 158, 11, 0.95)",
      border: "2px solid #d97706",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      color: "#1f2937",
      fontSize: 11,
      fontWeight: 600,
      textAlign: "center",
      padding: "6px 8px",
      cursor: "pointer",
    };
  }
  if (kind === "keyword") {
    return {
      width: 100,
      minHeight: 32,
      borderRadius: 6,
      background: "rgba(20, 184, 166, 0.9)",
      border: "2px solid #0d9488",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      color: "#fff",
      fontSize: 9,
      fontWeight: 600,
      textAlign: "center",
      padding: 4,
      cursor: "pointer",
    };
  }
  const score = (data?.impact_score as number | undefined) ?? 0;
  const size = 40 + Math.round(score * 60);
  const opacity = 0.5 + score * 0.5;
  return {
    width: size,
    height: size,
    borderRadius: "50%",
    background: `rgba(99, 102, 241, ${opacity})`,
    border: "2px solid #4f46e5",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    color: "#fff",
    fontSize: 10,
    textAlign: "center",
    padding: 4,
    cursor: "pointer",
  };
}

const GraphCanvas: React.FC<Props> = ({ seedDoi, depth = 2, expand }) => {
  const { nodes: rawNodes, edges: rawEdges, loading, error } = useGraphData(seedDoi, depth, expand);

  const [nodes, setNodes, onNodesChange] = useNodesState<GraphNode["data"]>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);
  const [selectedPaper, setSelectedPaper] = useState<PaperData | null>(null);

  // Transform API nodes → React Flow nodes with custom styling
  useEffect(() => {
    const rfNodes: Node[] = rawNodes.map((n) => ({
      id: n.id,
      position: { x: Math.random() * 600, y: Math.random() * 400 },
      data: {
        ...n.data,
        label: n.label ?? n.id,
        title: (n.data?.title as string | undefined) ?? n.label ?? n.id,
      },
      style: nodeStyle(n.data as Record<string, unknown> | undefined),
    }));
    setNodes(rfNodes);
    setEdges(rawEdges);
  }, [rawNodes, rawEdges, setNodes, setEdges]);

  const onConnect = useCallback(
    (params: Connection) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  );

  const onNodeClick = useCallback((_: React.MouseEvent, node: Node) => {
    const d = node.data as PaperData & { kind?: string };
    if (d.kind && d.kind !== "paper") return;
    if (!d.doi) return;
    setSelectedPaper(d as PaperData);
  }, []);

  if (loading) {
    return (
      <div
        style={{
          display: "flex",
          height: "100%",
          alignItems: "center",
          justifyContent: "center",
          color: "#818cf8",
        }}
      >
        Loading graph…
      </div>
    );
  }

  if (error) {
    return (
      <div
        style={{
          display: "flex",
          height: "100%",
          alignItems: "center",
          justifyContent: "center",
          color: "#f87171",
        }}
      >
        {error}
      </div>
    );
  }

  return (
    <div className="flex h-full w-full">
      {/* Graph canvas */}
      <div className="flex-1 h-full">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          onNodeClick={onNodeClick}
          fitView
        >
          <Background />
          <Controls />
          <MiniMap />
        </ReactFlow>
      </div>

      {/* Detail sidebar */}
      {selectedPaper && (
        <PaperDetail
          paper={selectedPaper}
          onClose={() => setSelectedPaper(null)}
        />
      )}
    </div>
  );
};

export default GraphCanvas;
