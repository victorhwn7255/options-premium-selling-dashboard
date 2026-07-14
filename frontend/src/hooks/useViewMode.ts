'use client';

import { useState, useEffect, useCallback } from 'react';

export type ViewMode = 'human' | 'machine';

const STORAGE_KEY = 'oh-view';

/**
 * [HUMAN|MACHINE] view mode. Mirrors useTheme's storage pattern ('oh-theme'),
 * with two deliberate differences:
 *
 * 1. No pre-paint script: theme is a DOM attribute CSS consumes, but view mode
 *    is a component-tree swap — React must hydrate the same tree the server
 *    rendered, so the first client render is always 'human' and the stored
 *    mode is applied in a mount effect. The swap is masked by the loading
 *    spinner both modes share.
 * 2. `?view=machine|human` forces the mode WITHOUT persisting it (a shared
 *    link shouldn't rewrite the recipient's preference). Only explicit toggle
 *    clicks write localStorage. Read via window.location.search — NOT
 *    useSearchParams, which would force a Suspense boundary on the page.
 */
export function useViewMode() {
  const [mode, setModeState] = useState<ViewMode>('human');

  const setMode = useCallback((m: ViewMode) => {
    setModeState(m);
    localStorage.setItem(STORAGE_KEY, m);
  }, []);

  useEffect(() => {
    const q = new URLSearchParams(window.location.search).get('view');
    if (q === 'machine' || q === 'human') { setModeState(q); return; }
    if (localStorage.getItem(STORAGE_KEY) === 'machine') setModeState('machine');
  }, []);

  return { mode, setMode } as const;
}
