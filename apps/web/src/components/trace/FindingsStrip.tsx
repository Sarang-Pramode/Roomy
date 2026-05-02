import type { FindingRow } from "@/api/client";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export function FindingsStrip({ findings, stepId }: { findings: FindingRow[]; stepId: string }) {
  const forStep = findings.filter((f) => f.step_id === stepId);
  const rest = findings.filter((f) => f.step_id !== stepId);
  const ordered = [...forStep, ...rest].slice(0, 12);

  if (ordered.length === 0) {
    return null;
  }

  return (
    <Card className="border-zinc-800 bg-zinc-900/60 text-zinc-100">
      <CardHeader className="pb-2">
        <CardTitle className="text-base font-semibold">Findings</CardTitle>
        <p className="text-xs font-normal text-zinc-500">Session diagnostics; matches this step shown first.</p>
      </CardHeader>
      <CardContent className="grid gap-2 sm:grid-cols-2">
        {ordered.map((f) => (
          <div
            key={f.finding_id}
            className={`rounded-lg border p-3 text-sm ${
              f.step_id === stepId ? "border-violet-500/40 bg-violet-950/30" : "border-zinc-800 bg-zinc-950/50"
            }`}
          >
            <div className="flex flex-wrap items-center gap-2">
              <Badge variant={f.severity === "warning" ? "default" : "secondary"}>{f.severity}</Badge>
              <span className="font-mono text-xs text-zinc-500">{f.finding_type}</span>
              {f.step_id === stepId ? (
                <span className="text-xs text-violet-400">this step</span>
              ) : f.step_id ? (
                <span className="text-xs text-zinc-600">step {f.step_id.slice(0, 8)}…</span>
              ) : null}
            </div>
            <p className="mt-1.5 text-zinc-300">{f.explanation}</p>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
