'use client';

interface RegimeSectionProps {
  regime: string;
  tagline: string;
  colorToken: 'error' | 'warning' | 'secondary' | 'accent';
  triggers: { metric: string; value: string }[];
  triggerLogic: string;
  explanation: string[];
  dos: string[];
  donts: string[];
  example: {
    tag: string;
    metrics: { label: string; value: string }[];
    narrative: string;
  };
  isCurrent: boolean;
}

const COLOR_MAP = {
  error: {
    border: 'border-l-error',
    bg: 'bg-error-subtle',
    text: 'text-error',
    bullet: 'bg-error',
    badge: 'bg-error text-txt-inverse',
  },
  warning: {
    border: 'border-l-warning',
    bg: 'bg-warning-subtle',
    text: 'text-warning',
    bullet: 'bg-warning',
    badge: 'bg-warning text-txt-inverse',
  },
  secondary: {
    border: 'border-l-secondary',
    bg: 'bg-secondary-subtle',
    text: 'text-secondary',
    bullet: 'bg-secondary',
    badge: 'bg-secondary text-txt-inverse',
  },
  accent: {
    border: 'border-l-accent',
    bg: 'bg-accent-subtle',
    text: 'text-accent',
    bullet: 'bg-accent',
    badge: 'bg-accent text-txt-inverse',
  },
} as const;

export default function RegimeSection({
  regime,
  tagline,
  colorToken,
  triggers,
  triggerLogic,
  explanation,
  dos,
  donts,
  example,
  isCurrent,
}: RegimeSectionProps) {
  const c = COLOR_MAP[colorToken];

  return (
    <section className={`relative border-l-4 ${c.border} ${c.bg} rounded-lg p-5 px-6`}>
      {/* Current badge */}
      {isCurrent && (
        <span className={`absolute top-4 right-4 ${c.badge} text-[10px] font-primary font-semibold tracking-widest uppercase px-2.5 py-1 rounded-full`}>
          CURRENT
        </span>
      )}

      {/* Header */}
      <h3 className={`font-secondary text-xl font-medium ${c.text} leading-tight`}>
        {regime}
      </h3>
      <p className="text-xs text-txt-secondary italic mt-1">{tagline}</p>

      {/* Triggers */}
      <div className="mt-4">
        <div className="flex items-center gap-2 mb-2">
          <span className="font-primary text-[10px] font-semibold text-txt-tertiary tracking-widest uppercase">
            Triggers
          </span>
          <span className="text-[10px] font-mono text-txt-tertiary">({triggerLogic})</span>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
          {triggers.map((t) => (
            <div key={t.metric} className="flex items-center gap-2">
              <span className={`w-1.5 h-1.5 rounded-full ${c.bullet} shrink-0`} />
              <span className="text-xs text-txt-secondary">
                <span className="font-mono font-medium text-txt">{t.metric}</span>{' '}
                {t.value}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Explanation */}
      <div className="mt-4 space-y-2">
        <span className="font-primary text-[10px] font-semibold text-txt-tertiary tracking-widest uppercase">
          What&apos;s Happening
        </span>
        {explanation.map((p, i) => (
          <p key={i} className="text-xs text-txt-secondary leading-relaxed">{p}</p>
        ))}
      </div>

      {/* DOs / DON'Ts */}
      <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <span className="font-primary text-[10px] font-semibold text-success tracking-widest uppercase mb-2 block">
            DOs
          </span>
          <ul className="space-y-1.5">
            {dos.map((d, i) => (
              <li key={i} className="flex items-start gap-2 text-xs text-txt-secondary leading-relaxed">
                <span className="text-success mt-0.5 shrink-0">&#10003;</span>
                {d}
              </li>
            ))}
          </ul>
        </div>
        <div>
          <span className="font-primary text-[10px] font-semibold text-error tracking-widest uppercase mb-2 block">
            DON&apos;Ts
          </span>
          <ul className="space-y-1.5">
            {donts.map((d, i) => (
              <li key={i} className="flex items-start gap-2 text-xs text-txt-secondary leading-relaxed">
                <span className="text-error mt-0.5 shrink-0">&#10007;</span>
                {d}
              </li>
            ))}
          </ul>
        </div>
      </div>

      {/* Example trade */}
      <div className="mt-4 bg-surface rounded-md border border-border p-4">
        <div className="flex items-center gap-2 mb-3">
          <span className="font-primary text-[10px] font-semibold text-txt-tertiary tracking-widest uppercase">
            Example
          </span>
          <span className={`text-[10px] font-mono ${c.text} px-2 py-0.5 rounded-full ${c.bg} border border-current`}>
            {example.tag}
          </span>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 mb-3">
          {example.metrics.map((m) => (
            <div key={m.label} className="bg-bg rounded-sm px-2.5 py-1.5 text-center">
              <span className="font-primary text-[10px] text-txt-tertiary tracking-wider uppercase block">
                {m.label}
              </span>
              <span className="font-mono text-xs font-semibold text-txt">{m.value}</span>
            </div>
          ))}
        </div>
        <p className="text-xs text-txt-secondary italic leading-relaxed">
          {example.narrative}
        </p>
      </div>
    </section>
  );
}
