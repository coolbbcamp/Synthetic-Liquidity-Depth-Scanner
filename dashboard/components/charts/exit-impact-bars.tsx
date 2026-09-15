"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { exitImpactAt100kWorstFirst } from "@/data/findings";

type Props = {
  title: string;
  caption: string;
};

export function ExitImpactBars({ title, caption }: Props) {
  const data = exitImpactAt100kWorstFirst();

  return (
    <figure className="chart-block">
      <h3>{title}</h3>
      <div style={{ width: "100%", height: 360 }}>
        <ResponsiveContainer>
          <BarChart data={data} layout="vertical" margin={{ left: 8, right: 16 }}>
            <CartesianGrid strokeDasharray="2 2" stroke="var(--chart-grid)" horizontal={false} />
            <XAxis type="number" tickFormatter={(v) => `${v}%`} />
            <YAxis type="category" dataKey="symbol" width={56} tick={{ fontSize: 11 }} />
            <Tooltip formatter={(v: number) => `${v.toFixed(2)}%`} />
            <Bar dataKey="impact" fill="var(--chart-line)" />
          </BarChart>
        </ResponsiveContainer>
      </div>
      <figcaption className="chart-caption">{caption}</figcaption>
    </figure>
  );
}
