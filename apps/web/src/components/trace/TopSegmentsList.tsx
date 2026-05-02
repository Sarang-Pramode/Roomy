import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { segmentHex, segmentLabel } from "@/lib/segmentColors";
import type { SegmentSummary } from "./ContextWindowCard";

export function TopSegmentsList({ summary }: { summary: SegmentSummary | null }) {
  const tops = summary?.top_segments;
  if (!tops || tops.length === 0) {
    return (
      <Card className="border-zinc-800 bg-zinc-900/60 text-zinc-100">
        <CardHeader className="pb-2">
          <CardTitle className="text-base font-semibold">Top segments by tokens</CardTitle>
          <p className="text-xs font-normal text-zinc-500">Ranked by estimated token count (not model “attention”).</p>
        </CardHeader>
      </Card>
    );
  }

  const maxTok = Math.max(...tops.map((t) => t.token_count ?? 0), 1);

  return (
    <Card className="border-zinc-800 bg-zinc-900/60 text-zinc-100">
      <CardHeader className="pb-2">
        <CardTitle className="text-base font-semibold">Top segments by tokens</CardTitle>
        <p className="text-xs font-normal text-zinc-500">Share of input segments by token estimate.</p>
      </CardHeader>
      <CardContent className="space-y-3">
        {tops.map((t) => {
          const n = t.token_count ?? 0;
          const w = (n / maxTok) * 100;
          return (
            <div key={t.segment_type} className="space-y-1">
              <div className="flex justify-between text-xs">
                <span className="text-zinc-300">{segmentLabel(t.segment_type)}</span>
                <span className="tabular-nums text-zinc-500">{n.toLocaleString()} tok</span>
              </div>
              <div className="h-2 overflow-hidden rounded-full bg-zinc-800">
                <div className="h-full rounded-full" style={{ width: `${w}%`, backgroundColor: segmentHex(t.segment_type) }} />
              </div>
            </div>
          );
        })}
      </CardContent>
    </Card>
  );
}
