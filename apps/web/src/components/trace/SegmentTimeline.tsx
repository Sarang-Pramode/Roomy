import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { SegmentRow } from "@/api/client";
import { segmentHex, segmentLabel } from "@/lib/segmentColors";

export function SegmentTimeline({ segments }: { segments: SegmentRow[] }) {
  if (segments.length === 0) {
    return null;
  }

  const sorted = [...segments].sort((a, b) => a.order_index - b.order_index);
  const total = sorted.reduce((s, r) => s + (r.token_count ?? 0), 0) || 1;

  return (
    <Card className="border-zinc-800 bg-zinc-900/60 text-zinc-100">
      <CardHeader className="pb-2">
        <CardTitle className="text-base font-semibold">Token order in context</CardTitle>
        <p className="text-xs font-normal text-zinc-500">Width ∝ segment token count along prompt order.</p>
      </CardHeader>
      <CardContent>
        <div className="flex h-10 w-full overflow-hidden rounded-md border border-zinc-800 bg-zinc-950">
          {sorted.map((r) => {
            const w = Math.max(((r.token_count ?? 0) / total) * 100, 0.8);
            return (
              <div
                key={r.segment_id}
                title={`#${r.order_index} ${segmentLabel(r.segment_type)} — ${r.token_count ?? 0} tok`}
                className="min-w-px border-r border-zinc-900/80 last:border-r-0"
                style={{ width: `${w}%`, backgroundColor: segmentHex(r.segment_type) }}
              />
            );
          })}
        </div>
        <p className="mt-2 text-xs text-zinc-600">Less context ← position → More context (later segments often closer to the model decision).</p>
      </CardContent>
    </Card>
  );
}
