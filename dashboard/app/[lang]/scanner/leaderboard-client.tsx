"use client";

import { useEffect, useState } from "react";
import type { Dictionary } from "@/i18n/get-dictionary";
import { fetchLeaderboard, LeaderboardEntry } from "@/lib/api";

type Props = {
  dict: Dictionary["scanner"];
  common: Dictionary["common"];
  locale: string;
};

export function LeaderboardClient({ dict, common, locale }: Props) {
  const [rows, setRows] = useState<LeaderboardEntry[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchLeaderboard()
      .then(setRows)
      .catch((e) => setError(e.message));
  }, []);

  const prefix = `/${locale}/scanner`;

  return (
    <div>
      <h1>{dict.leaderboardTitle}</h1>
      <p className="muted">{dict.leaderboardSubtitle}</p>
      {error && <div className="panel">{common.apiUnavailable}: {error}</div>}
      <div className="panel">
        <table>
          <thead>
            <tr>
              <th>{dict.columns.mint}</th>
              <th>{dict.columns.grade}</th>
              <th>{dict.columns.exit95}</th>
              <th>{dict.columns.mcapExit}</th>
              <th>{dict.columns.cliff}</th>
              <th>{dict.columns.noRoute}</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.mint}>
                <td>
                  <a href={`${prefix}/asset/${row.mint}`}>{row.mint.slice(0, 8)}…</a>
                </td>
                <td className={`grade-${row.grade || "D"}`}>{row.grade || "-"}</td>
                <td>{row.exit_capacity_95 ? `$${row.exit_capacity_95.toLocaleString()}` : "-"}</td>
                <td>{row.mcap_exit_ratio ? row.mcap_exit_ratio.toFixed(1) : "-"}</td>
                <td>{row.cliff_detected ? common.yes : common.no}</td>
                <td>{row.no_route_ceiling ? `$${row.no_route_ceiling.toLocaleString()}` : "-"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
