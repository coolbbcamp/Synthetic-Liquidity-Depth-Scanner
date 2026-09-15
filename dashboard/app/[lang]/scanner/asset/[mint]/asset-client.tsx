"use client";

import { useEffect, useState } from "react";
import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { Dictionary } from "@/i18n/get-dictionary";
import { AssetDetail, fetchAsset } from "@/lib/api";

type Props = {
  mint: string;
  dict: Dictionary["scanner"];
  common: Dictionary["common"];
};

export function AssetClient({ mint, dict, common }: Props) {
  const [asset, setAsset] = useState<AssetDetail | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchAsset(mint)
      .then(setAsset)
      .catch((e) => setError(e.message));
  }, [mint]);

  if (error) return <div className="panel">{dict.failedLoad}: {error}</div>;
  if (!asset) return <div className="panel">{common.loading}</div>;

  const chartData = asset.latest_rungs
    .filter((r) => !r.no_route && r.out_usd)
    .map((r) => ({
      notional: r.notional_usd,
      efficiencyPct: ((r.out_usd || 0) / r.notional_usd) * 100,
      route: r.route_labels,
    }));

  return (
    <div>
      <h1>
        {asset.symbol} <span className="muted">({asset.kind})</span>
      </h1>
      <p className="muted">
        {asset.name} · quote {asset.quote_symbol || "USDC"} · tier {asset.tier}
      </p>

      <div className="panel">
        <h3>{dict.latestScore}</h3>
        {asset.latest_score ? (
          <p>
            Grade{" "}
            <span className={`grade-${asset.latest_score.grade || "D"}`}>
              {asset.latest_score.grade}
            </span>
            · exit @95% ${asset.latest_score.exit_capacity_95?.toLocaleString() || "-"}
            · cliff {asset.latest_score.cliff_detected ? common.yes : common.no}
          </p>
        ) : (
          <p>{dict.noScore}</p>
        )}
      </div>

      <div className="panel">
        <h3>{dict.exitCurve}</h3>
        <div style={{ width: "100%", height: 280 }}>
          <ResponsiveContainer>
            <LineChart data={chartData}>
              <XAxis dataKey="notional" tickFormatter={(v) => `$${v / 1000}k`} />
              <YAxis domain={[0, 105]} tickFormatter={(v) => `${v}%`} />
              <Tooltip formatter={(v: number) => `${v.toFixed(2)}%`} />
              <Line type="monotone" dataKey="efficiencyPct" stroke="var(--chart-line)" dot />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="panel">
        <h3>{dict.routeTable}</h3>
        <table>
          <thead>
            <tr>
              <th>{dict.routeCols.notional}</th>
              <th>{dict.routeCols.cashOut}</th>
              <th>{dict.routeCols.efficiency}</th>
              <th>{dict.routeCols.route}</th>
              <th>{dict.routeCols.bindingLeg}</th>
            </tr>
          </thead>
          <tbody>
            {asset.latest_rungs.map((r) => (
              <tr key={r.notional_usd}>
                <td>${r.notional_usd.toLocaleString()}</td>
                <td>{r.no_route ? dict.noRoute : `$${(r.out_usd || 0).toLocaleString()}`}</td>
                <td>{r.efficiency != null ? `${(r.efficiency * 100).toFixed(2)}%` : "-"}</td>
                <td>{r.route_labels}</td>
                <td>{r.binding_leg || "-"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
