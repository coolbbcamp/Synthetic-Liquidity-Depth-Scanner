"use client";

import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { strcxCliffSeries } from "@/data/findings";

type Props = {
  title: string;
  caption: string;
  notionalAxis: string;
  priceAxis: string;
};

export function CliffChart({ title, caption, notionalAxis, priceAxis }: Props) {
  const data = strcxCliffSeries.map((p) => ({
    notional: p.notional,
    price: p.executionPrice,
    route: p.route,
  }));

  return (
    <figure className="chart-block">
      <h3>{title}</h3>
      <div style={{ width: "100%", height: 320 }}>
        <ResponsiveContainer>
          <LineChart data={data} margin={{ bottom: 24, left: 8, right: 16 }}>
            <CartesianGrid strokeDasharray="2 2" stroke="var(--chart-grid)" />
            <XAxis
              dataKey="notional"
              tickFormatter={(v) => `$${v / 1000}k`}
              label={{ value: notionalAxis, position: "bottom", offset: 0, fontSize: 11 }}
            />
            <YAxis
              tickFormatter={(v) => `$${v}`}
              label={{ value: priceAxis, angle: -90, position: "insideLeft", fontSize: 11 }}
            />
            <Tooltip
              formatter={(v: number) => `$${v.toFixed(3)}`}
              labelFormatter={(l) => `$${Number(l).toLocaleString()}`}
            />
            <Line
              type="monotone"
              dataKey="price"
              stroke="var(--chart-line)"
              strokeWidth={2}
              dot={{ r: 4 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
      <figcaption className="chart-caption">{caption}</figcaption>
    </figure>
  );
}
