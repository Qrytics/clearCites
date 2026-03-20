import { useCallback, useState } from "react";

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

interface NavigationState {
  history: PaperData[];
  current: PaperData | null;
  canGoBack: boolean;
  canGoForward: boolean;
}

/**
 * Manages browser-style forward/back navigation through visited paper nodes.
 */
export function useGraphNavigation(): NavigationState & {
  navigate: (paper: PaperData) => void;
  goBack: () => void;
  goForward: () => void;
} {
  const [history, setHistory] = useState<PaperData[]>([]);
  const [index, setIndex] = useState<number>(-1);

  const navigate = useCallback((paper: PaperData) => {
    setHistory((prev) => {
      // Drop any forward history when navigating to a new node
      const trimmed = prev.slice(0, index + 1);
      return [...trimmed, paper];
    });
    setIndex((prev) => prev + 1);
  }, [index]);

  const goBack = useCallback(() => {
    setIndex((prev) => Math.max(0, prev - 1));
  }, []);

  const goForward = useCallback(() => {
    setIndex((prev) => Math.min(history.length - 1, prev + 1));
  }, [history.length]);

  return {
    history,
    current: index >= 0 ? history[index] ?? null : null,
    canGoBack: index > 0,
    canGoForward: index < history.length - 1,
    navigate,
    goBack,
    goForward,
  };
}
