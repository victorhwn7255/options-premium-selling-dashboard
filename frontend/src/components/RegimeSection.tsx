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
    border: 'border-l-8 border-black',
    bg: 'bg-[#F5F5F5]',
    text: 'text-black',
    bullet: 'bg-black',
    badge: 'bg-black text-white',
  },
  warning: {
    border: 'border-l-4 border-black',
    bg: 'bg-[#F5F5F5]',
    text: 'text-black',
    bullet: 'bg-black',
    badge: 'bg-black text-white',
  },
  secondary: {
    border: 'border-l-2 border-black',
    bg: 'bg-white',
    text: 'text-black',
    bullet: 'bg-black',
    badge: 'border border-black text-black',
  },
  accent: {
    border: 'border-l-2 border-[#E5E5E5]',
    bg: 'bg-white',
    text: 'text-black',
    bullet: 'bg-[#525252]',
    badge: 'border border-black text-black',
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
    <section className={`relative ${c.border} ${c.bg} p-5 px-6`}>
      {/* Current badge */}
      {isCurrent && (
        <span className={`absolute top-4 right-4 ${c.badge} text-[10px] font-mono font-semibold tracking-widest uppercase px-2.5 py-1`}>
          CURRENT
        </span>
      )}

      {/* Header */}
      <h3 className={`font-display text-xl font-bold ${c.text} leading-tight`}>
        {regime}
      </h3>
      <p className="text-xs text-[#525252] italic mt-1 font-body">{tagline}</p>

      {/* Triggers */}
      <div className="mt-4">
        <div className="flex items-center gap-2 mb-2">
          <span className="font-mono text-[10px] font-semibold text-[#525252] tracking-widest uppercase">
            Triggers
          </span>
          <span className="text-[10px] font-mono text-[#525252]">({triggerLogic})</span>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
          {triggers.map((t) => (
            <div key={t.metric} className="flex items-center gap-2">
              <span className={`w-1.5 h-1.5 ${c.bullet} shrink-0`} />
              <span className="text-xs text-[#525252] font-body">
                <span className="font-mono font-medium text-black">{t.metric}</span>{' '}
                {t.value}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Explanation */}
      <div className="mt-4 space-y-2">
        <span className="font-mono text-[10px] font-semibold text-[#525252] tracking-widest uppercase">
          What&apos;s Happening
        </span>
        {explanation.map((p, i) => (
          <p key={i} className="text-xs text-[#525252] leading-relaxed font-body">{p}</p>
        ))}
      </div>

      {/* DOs / DON'Ts */}
      <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <span className="font-mono text-[10px] font-semibold text-black tracking-widest uppercase mb-2 block">
            DOs
          </span>
          <ul className="space-y-1.5">
            {dos.map((d, i) => (
              <li key={i} className="flex items-start gap-2 text-xs text-[#525252] leading-relaxed font-body">
                <span className="text-black mt-0.5 shrink-0">&#10003;</span>
                {d}
              </li>
            ))}
          </ul>
        </div>
        <div>
          <span className="font-mono text-[10px] font-semibold text-black tracking-widest uppercase mb-2 block">
            DON&apos;Ts
          </span>
          <ul className="space-y-1.5">
            {donts.map((d, i) => (
              <li key={i} className="flex items-start gap-2 text-xs text-[#525252] leading-relaxed font-body">
                <span className="text-black mt-0.5 shrink-0">&#10007;</span>
                {d}
              </li>
            ))}
          </ul>
        </div>
      </div>

      {/* Example trade */}
      <div className="mt-4 bg-white border border-black p-4">
        <div className="flex items-center gap-2 mb-3">
          <span className="font-mono text-[10px] font-semibold text-[#525252] tracking-widest uppercase">
            Example
          </span>
          <span className="text-[10px] font-mono text-black px-2 py-0.5 border border-black">
            {example.tag}
          </span>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 mb-3">
          {example.metrics.map((m) => (
            <div key={m.label} className="bg-[#F5F5F5] px-2.5 py-1.5 text-center">
              <span className="font-mono text-[10px] text-[#525252] tracking-wider uppercase block">
                {m.label}
              </span>
              <span className="font-mono text-xs font-semibold text-black">{m.value}</span>
            </div>
          ))}
        </div>
        <p className="text-xs text-[#525252] italic leading-relaxed font-body">
          {example.narrative}
        </p>
      </div>
    </section>
  );
}
