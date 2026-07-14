'use client';

import type { MachineSection } from '@/lib/machine-format';
import { fmtValue } from '@/lib/machine-format';

/**
 * Renders one MachineSection descriptor — the same structure the COPY_ALL
 * serializer walks, so screen and clipboard cannot drift. Deliberately
 * design-free: monospace, verbatim values, no badges/colors/icons.
 * Every table scrolls inside its own container; the page never scrolls
 * horizontally.
 */
export default function MachineSectionView({ section }: { section: MachineSection }) {
  return (
    <section className="mb-6">
      <h2 className="font-mono text-2xs tracking-widest text-txt-tertiary border-b border-border-subtle pb-1 mb-2 whitespace-nowrap overflow-hidden">
        {'== '}{section.id}{' =='}
        {section.note && <span className="ml-2 normal-case">{section.note}</span>}
      </h2>

      {section.kind === 'kv' ? (
        section.rows.length > 0 && (
          <dl className="font-mono text-2xs sm:text-xs">
            {section.rows.map(([k, v], i) => (
              <div key={`${k}-${i}`} className="flex gap-3 py-px">
                <dt className="text-txt-secondary shrink-0 min-w-[220px]">{k}:</dt>
                <dd className="text-txt break-all">{fmtValue(v)}</dd>
              </div>
            ))}
          </dl>
        )
      ) : (
        section.rows.length > 0 && (
          <div className="overflow-x-auto border border-border-subtle rounded-sm">
            <table className="font-mono text-2xs sm:text-xs border-collapse w-full">
              <thead>
                <tr className="bg-surface-alt text-left">
                  {section.columns.map(c => (
                    <th key={c} className="px-2 py-1 font-normal text-txt-secondary whitespace-nowrap border-b border-border-subtle">
                      {c}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {section.rows.map((row, ri) => (
                  <tr key={ri} className={ri % 2 === 1 ? 'bg-surface-alt' : undefined}>
                    {row.map((v, ci) => (
                      <td key={ci} className="px-2 py-0.5 whitespace-nowrap tabular-nums text-txt">
                        {fmtValue(v)}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )
      )}
    </section>
  );
}
