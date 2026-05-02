import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { segmentHex, segmentLabel } from "@/lib/segmentColors";

export type SegmentSummary = {
  total_input_tokens_estimated?: number;
  percent_by_segment_type?: Record<string, number>;
  top_segments?: { segment_type: string; token_count: number | null }[];
};

export function ContextWindowCard({ summary }: { summary: SegmentSummary | null }) {
  const pct = summary?.percent_by_segment_type;
  const total = summary?.total_input_tokens_estimated;

  if (!pct || Object.keys(pct).length === 0) {
    return (
      <Card className="border-zinc-800 bg-zinc-900/60 text-zinc-100">
        <CardHeader className="pb-2">
          <CardTitle className="text-base font-semibold">Context window</CardTitle>
          <p className="text-xs font-normal text-zinc-500">No segment summary for this step.</p>
        </CardHeader>
      </Card>
    );
  }

  const entries = Object.entries(pct).sort((a, b) => b[1] - a[1]);

  return (
    <Card className="border-zinc-800 bg-zinc-900/60 text-zinc-100">
      <CardHeader className="pb-2">
        <div className="flex flex-wrap items-baseline justify-between gap-2">
          <CardTitle className="text-base font-semibold">Context window</CardTitle>
          <span className="text-xs text-zinc-500">Estimated input context</span>
        </div>
        <p className="text-2xl font-semibold tabular-nums text-zinc-100">
          {total != null ? total.toLocaleString() : "—"}{" "}
          <span className="text-sm font-normal text-zinc-500">tokens</span>
        </p>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="flex h-4 w-full overflow-hidden rounded-md bg-zinc-800">
          {entries.map(([k, v]) => (
            <div
              key={k}
              title={`${segmentLabel(k)}: ${v.toFixed(1)}%`}
              className="min-w-[2px] transition-opacity hover:opacity-90"
              style={{ width: `${Math.max(v, 0)}%`, backgroundColor: segmentHex(k) }}
            />
          ))}
        </div>
        <ul className="flex flex-wrap gap-x-4 gap-y-2 text-xs text-zinc-400">
          {entries.map(([k, v]) => (
            <li key={k} className="flex items-center gap-1.5">
              <span className="h-2.5 w-2.5 shrink-0 rounded-sm" style={{ backgroundColor: segmentHex(k) }} />
              <span className="text-zinc-300">{segmentLabel(k)}</span>
              <span className="tabular-nums text-zinc-500">{v.toFixed(0)}%</span>
            </li>
          ))}
        </ul>
      </CardContent>
    </Card>
  );
}
