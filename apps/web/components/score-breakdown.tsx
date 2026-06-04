import type { MatchReport } from "@/lib/types";
import { formatBreakdownValue } from "@/lib/format";

type ScoreBreakdownProps = {
  breakdown: MatchReport["score_breakdown"];
};

export function ScoreBreakdown({ breakdown }: ScoreBreakdownProps) {
  const entries = Object.entries(breakdown);

  if (!entries.length) {
    return <p className="empty-state">No score breakdown available yet.</p>;
  }

  return (
    <table className="breakdown-table">
      <tbody>
        {entries.map(([key, value]) => (
          <tr key={key}>
            <th>{key}</th>
            <td>{formatBreakdownValue(value)}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
