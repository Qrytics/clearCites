import React, { useCallback, useEffect, useRef, useState } from "react";
import ReactFlow, {
  addEdge,
  Background,
  Connection,
  Controls,
  Edge,
  MiniMap,
  Node,
  ReactFlowProvider,
  useEdgesState,
  useNodesState,
  useReactFlow,
} from "reactflow";
import "reactflow/dist/style.css";

import PaperDetail from "./PaperDetail";
import { layoutWithDagre } from "../lib/graphLayout";
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

const GraphCanvasInner: React.FC<Props> = ({ seedDoi, depth = 2, expand }) => {
  const { nodes: rawNodes, edges: rawEdges, loading, error } = useGraphData(seedDoi, depth, expand);
  const { fitView } = useReactFlow();

  const [nodes, setNodes, onNodesChange] = useNodesState<GraphNode["data"]>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);
  const [selectedPaper, setSelectedPaper] = useState<PaperData | null>(null);
  const shellRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const styled: Node[] = rawNodes.map((n) => ({
      id: n.id,
      position: { x: 0, y: 0 },
      data: {
        ...n.data,
        label: n.label ?? n.id,
        title: (n.data?.title as string | undefined) ?? n.label ?? n.id,
      },
      style: nodeStyle(n.data as Record<string, unknown> | undefined),
    }));
    const laidOut = layoutWithDagre(styled, rawEdges);
    setNodes(laidOut);
    setEdges(rawEdges);
  }, [rawNodes, rawEdges, setNodes, setEdges]);

  useEffect(() => {
    if (!nodes.length) return;
    const id = window.requestAnimationFrame(() => {
      fitView({ padding: 0.18, maxZoom: 1.2, duration: 220 });
    });
    return () => window.cancelAnimationFrame(id);
  }, [nodes, fitView, seedDoi]);

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

  const toggleFullscreen = useCallback(() => {
    const el = shellRef.current;
    if (!el) return;
    if (!document.fullscreenElement) {
      void el.requestFullscreen();
    } else {
      void document.exitFullscreen();
    }
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

  const btnStyle: React.CSSProperties = {
    fontSize: 11,
    fontWeight: 600,
    padding: "4px 10px",
    borderRadius: 6,
    border: "1px solid #4f46e5",
    background: "rgba(30, 27, 75, 0.85)",
    color: "#c7d2fe",
    cursor: "pointer",
  };

  return (
    <div
      style={{
        position: "absolute",
        inset: 0,
        display: "flex",
        minHeight: 0,
      }}
    >
      <div
        ref={shellRef}
        style={{
          display: "flex",
          flex: 1,
          flexDirection: "column",
          minHeight: 0,
          background: "#0b1020",
        }}
      >
        <div
          style={{
            display: "flex",
            justifyContent: "flex-end",
            alignItems: "center",
            gap: 8,
            padding: "6px 8px",
            borderBottom: "1px solid rgba(79, 70, 229, 0.35)",
            background: "rgba(15, 23, 42, 0.5)",
          }}
        >
          <button type="button" style={btnStyle} onClick={toggleFullscreen}>
            Full screen
          </button>
        </div>
        <div style={{ flex: 1, minHeight: 0, position: "relative" }}>
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            onNodeClick={onNodeClick}
            fitView={false}
            minZoom={0.08}
            maxZoom={1.6}
            style={{ width: "100%", height: "100%" }}
          >
            <Background />
            <Controls />
            <MiniMap />
          </ReactFlow>
        </div>
      </div>

      {selectedPaper && (
        <PaperDetail paper={selectedPaper} onClose={() => setSelectedPaper(null)} />
      )}
    </div>
  );
};

const GraphCanvas: React.FC<Props> = (props) => (
  <ReactFlowProvider>
    <GraphCanvasInner {...props} />
  </ReactFlowProvider>
);

export default GraphCanvas;
