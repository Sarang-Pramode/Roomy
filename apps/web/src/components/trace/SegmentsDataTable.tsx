import type { SegmentRow } from "@/api/client";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { segmentHex, segmentLabel } from "@/lib/segmentColors";

export function SegmentsDataTable({ segments }: { segments: SegmentRow[] }) {
  if (segments.length === 0) {
    return <p className="text-sm text-zinc-500">No segments (non-LLM step or capture pending).</p>;
  }

  const sorted = [...segments].sort((a, b) => a.order_index - b.order_index);

  return (
    <Table>
      <TableHeader>
        <TableRow className="border-zinc-800 hover:bg-transparent">
          <TableHead className="w-12 text-zinc-500">#</TableHead>
          <TableHead className="text-zinc-500">Type</TableHead>
          <TableHead className="text-zinc-500">Source</TableHead>
          <TableHead className="text-right text-zinc-500">Tokens</TableHead>
          <TableHead className="text-zinc-500">Preview</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {sorted.map((r) => (
          <TableRow key={r.segment_id} className="border-zinc-800 hover:bg-zinc-800/30">
            <TableCell className="tabular-nums text-zinc-500">{r.order_index}</TableCell>
            <TableCell>
              <Badge
                variant="outline"
                className="border-0 font-normal text-zinc-200"
                style={{ backgroundColor: `${segmentHex(r.segment_type)}22`, borderColor: segmentHex(r.segment_type) }}
              >
                {segmentLabel(r.segment_type)}
              </Badge>
            </TableCell>
            <TableCell className="max-w-[140px] truncate text-xs text-zinc-500">{r.source_name || "—"}</TableCell>
            <TableCell className="text-right tabular-nums text-zinc-300">{r.token_count ?? "—"}</TableCell>
            <TableCell className="max-w-xl whitespace-pre-wrap text-xs text-zinc-400">{r.text_preview}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
