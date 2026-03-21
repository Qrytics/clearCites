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
  data: PaperData & { label: string };
}

interface Props {
  seedDoi: string;
  depth?: number;
}

/** Scale node size based on the paper's impact_score (0–1). */
function nodeStyle(impactScore: number | undefined): React.CSSProperties {
  const score = impactScore ?? 0;
  const size = 40 + Math.round(score * 60); // 40 px – 100 px
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

const GraphCanvas: React.FC<Props> = ({ seedDoi, depth = 2 }) => {
  const { nodes: rawNodes, edges: rawEdges, loading, error } = useGraphData(seedDoi, depth);

  const [nodes, setNodes, onNodesChange] = useNodesState<GraphNode["data"]>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);
  const [selectedPaper, setSelectedPaper] = useState<PaperData | null>(null);

  // Transform API nodes → React Flow nodes with custom styling
  useEffect(() => {
    const rfNodes: Node[] = rawNodes.map((n) => ({
      id: n.id,
      position: { x: Math.random() * 600, y: Math.random() * 400 },
      data: { label: n.label ?? n.id, ...n.data },
      style: nodeStyle(n.data?.impact_score),
    }));
    setNodes(rfNodes);
    setEdges(rawEdges);
  }, [rawNodes, rawEdges, setNodes, setEdges]);

  const onConnect = useCallback(
    (params: Connection) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  );

  const onNodeClick = useCallback(
    (_: React.MouseEvent, node: Node) => {
      setSelectedPaper(node.data as PaperData);
    },
    []
  );

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center text-indigo-400">
        Loading graph…
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex h-full items-center justify-center text-red-400">
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
