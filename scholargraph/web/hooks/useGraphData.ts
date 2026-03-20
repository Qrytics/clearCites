import { useCallback, useEffect, useState } from "react";
import { Edge } from "reactflow";

interface RawNode {
  id: string;
  label: string;
  data: Record<string, unknown>;
}

interface GraphState {
  nodes: RawNode[];
  edges: Edge[];
  loading: boolean;
  error: string | null;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

/**
 * Fetches graph data (nodes + edges) for a seed DOI from the backend API
 * and re-fetches whenever seedDoi or depth changes.
 */
export function useGraphData(seedDoi: string, depth = 2): GraphState {
  const [state, setState] = useState<GraphState>({
    nodes: [],
    edges: [],
    loading: false,
    error: null,
  });

  const fetchGraph = useCallback(async () => {
    if (!seedDoi) return;
    setState((prev) => ({ ...prev, loading: true, error: null }));
    try {
      const params = new URLSearchParams({ doi: seedDoi, depth: String(depth) });
      const res = await fetch(`${API_BASE}/graph?${params.toString()}`);
      if (!res.ok) {
        throw new Error(`API responded with ${res.status}: ${res.statusText}`);
      }
      const data: { nodes: RawNode[]; edges: Edge[] } = await res.json();
      setState({ nodes: data.nodes ?? [], edges: data.edges ?? [], loading: false, error: null });
    } catch (err) {
      setState((prev) => ({
        ...prev,
        loading: false,
        error: err instanceof Error ? err.message : "Unknown error",
      }));
    }
  }, [seedDoi, depth]);

  useEffect(() => {
    fetchGraph();
  }, [fetchGraph]);

  return state;
}
