"use client";

import {
  CartesianGrid,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
  ZAxis,
} from "recharts";
import { correlations, tvlScatterData } from "@/data/findings";

type Props = {
  title: string;
  caption: string;
  tvlAxis: string;
  impactAxis: string;
};

export function TvlVsExitScatter({ title, caption, tvlAxis, impactAxis }: Props) {
  const data = tvlScatterData();

  return (
    <figure className="chart-block">
      <h3>{title}</h3>
      <div style={{ width: "100%", height: 360 }}>
        <ResponsiveContainer>
          <ScatterChart margin={{ bottom: 24, left: 8, right: 16 }}>
            <CartesianGrid strokeDasharray="2 2" stroke="var(--chart-grid)" />
            <XAxis
              type="number"
              dataKey="tvlPct"
              name={tvlAxis}
              tickFormatter={(v) => `${v}%`}
              label={{ value: tvlAxis, position: "bottom", offset: 0, fontSize: 11 }}
            />
            <YAxis
              type="number"
              dataKey="impact"
              name={impactAxis}
              tickFormatter={(v) => `${v}%`}
              label={{ value: impactAxis, angle: -90, position: "insideLeft", fontSize: 11 }}
            />
            <ZAxis range={[60, 60]} />
            <Tooltip
              cursor={{ strokeDasharray: "2 2" }}
              formatter={(v: number, name: string) =>
                name === "tvlPct" ? `${v.toFixed(2)}%` : `${v.toFixed(2)}%`
              }
              labelFormatter={(_, payload) =>
                payload?.[0]?.payload?.symbol ? String(payload[0].payload.symbol) : ""
              }
            />
            <Scatter data={data} fill="var(--chart-line)" />
          </ScatterChart>
        </ResponsiveContainer>
      </div>
      <figcaption className="chart-caption">
        {caption} (ρ TVL/mcap = {correlations.tvlMcapRho}; ρ absolute TVL ={" "}
        {correlations.absoluteTvlRho})
      </figcaption>
    </figure>
  );
}
