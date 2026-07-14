'use client';

import type { ViewMode } from '@/hooks/useViewMode';

/**
 * Paxel-style checkbox toggle: `[X] HUMAN  [ ] MACHINE`.
 * Two independently tabbable buttons with aria-pressed (simpler and equally
 * accessible vs a roving-tabindex radiogroup). whitespace-pre keeps `[ ]`
 * from collapsing so widths never shift on toggle.
 */
export default function ViewModeToggle({ mode, onChange }: {
  mode: ViewMode;
  onChange: (m: ViewMode) => void;
}) {
  return (
    <div className="font-mono text-[12px] tracking-wider flex items-center gap-2 select-none whitespace-pre">
      {(['human', 'machine'] as const).map(m => (
        <button
          key={m}
          aria-pressed={mode === m}
          onClick={() => onChange(m)}
          className={`transition-colors ${
            mode === m ? 'text-txt font-medium' : 'text-txt-tertiary hover:text-txt'
          }`}
        >
          {mode === m ? '[X]' : '[ ]'} {m.toUpperCase()}
        </button>
      ))}
    </div>
  );
}
