import { segmentHex, segmentLabel } from "@/lib/segmentColors";
import type { SegmentSummary } from "./ContextWindowCard";

/** Donut ring using conic-gradient + inner disc. */
export function CompositionDonut({ summary }: { summary: SegmentSummary | null }) {
  const pct = summary?.percent_by_segment_type;
  if (!pct || Object.keys(pct).length === 0) return null;

  const entries = Object.entries(pct).sort((a, b) => b[1] - a[1]);
  let acc = 0;
  const stops: string[] = [];
  for (const [k, v] of entries) {
    const start = acc;
    acc += v;
    stops.push(`${segmentHex(k)} ${start}% ${acc}%`);
  }
  const gradient = `conic-gradient(${stops.join(", ")})`;

  return (
    <div className="flex flex-col items-center gap-3">
      <div className="relative h-28 w-28">
        <div className="absolute inset-0 rounded-full" style={{ background: gradient }} />
        <div className="absolute inset-[18%] rounded-full bg-zinc-950" />
      </div>
      <ul className="w-full max-w-[200px] space-y-1 text-xs text-zinc-400">
        {entries.map(([k, v]) => (
          <li key={k} className="flex justify-between gap-2">
            <span className="flex min-w-0 items-center gap-1.5">
              <span className="h-2 w-2 shrink-0 rounded-full" style={{ backgroundColor: segmentHex(k) }} />
              <span className="truncate text-zinc-300">{segmentLabel(k)}</span>
            </span>
            <span className="shrink-0 tabular-nums text-zinc-500">{v.toFixed(0)}%</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
