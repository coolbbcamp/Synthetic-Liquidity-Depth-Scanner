"use client";

import { useEffect, useState } from "react";
import type { Dictionary } from "@/i18n/get-dictionary";
import { Asset, fetchAssets, fetchExitQuote } from "@/lib/api";

type Props = {
  dict: Dictionary["scanner"];
};

export function CalculatorClient({ dict }: Props) {
  const [assets, setAssets] = useState<Asset[]>([]);
  const [mint, setMint] = useState("");
  const [notional, setNotional] = useState(100000);
  const [result, setResult] = useState<{
    notional_usd: number;
    matched_notional_usd: number;
    no_route: boolean;
    cash_usd: number | null;
    route_labels: string;
    binding_leg: string | null;
  } | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchAssets().then(setAssets).catch((e) => setError(e.message));
  }, []);

  async function run() {
    setError(null);
    try {
      const quote = await fetchExitQuote(mint, notional);
      setResult(quote);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Unknown error");
    }
  }

  return (
    <div>
      <h1>{dict.calculatorTitle}</h1>
      <p className="muted">{dict.calculatorSubtitle}</p>
      <div className="panel" style={{ display: "grid", gap: 12, maxWidth: 520 }}>
        <select value={mint} onChange={(e) => setMint(e.target.value)}>
          <option value="">{dict.selectAsset}</option>
          {assets.map((a) => (
            <option key={a.mint} value={a.mint}>
              {a.symbol} ({a.kind})
            </option>
          ))}
        </select>
        <input
          type="number"
          value={notional}
          onChange={(e) => setNotional(Number(e.target.value))}
        />
        <button type="button" onClick={run} disabled={!mint}>
          {dict.calculate}
        </button>
      </div>
      {error && <div className="panel">Error: {error}</div>}
      {result && (
        <div className="panel">
          <p>{dict.requested}: ${result.notional_usd.toLocaleString()}</p>
          <p>{dict.matchedRung}: ${result.matched_notional_usd.toLocaleString()}</p>
          <p>
            {dict.cashOut}:{" "}
            {result.no_route ? dict.noRoute : `$${(result.cash_usd || 0).toLocaleString()}`}
          </p>
          <p>{dict.routeCols.route}: {result.route_labels}</p>
          <p>{dict.bindingLeg}: {result.binding_leg || "-"}</p>
        </div>
      )}
    </div>
  );
}
