"use client";

import { useEffect, useMemo, useState } from "react";
import type { Dictionary } from "@/i18n/get-dictionary";
import { Asset, fetchAssets, fetchExitQuote } from "@/lib/api";

type Props = {
  dict: Dictionary["scanner"];
};

function AssetPicker({
  probed,
  awaiting,
  value,
  onChange,
  dict,
}: {
  probed: Asset[];
  awaiting: Asset[];
  value: string;
  onChange: (mint: string) => void;
  dict: Dictionary["scanner"];
}) {
  return (
    <div className="calculator-asset-picker" role="listbox" aria-label={dict.selectAsset}>
      {probed.length > 0 && (
        <div className="calculator-asset-group">
          <div className="calculator-asset-group-label probed">{dict.probedAssetsGroup}</div>
          {probed.map((a) => (
            <button
              type="button"
              key={a.mint}
              role="option"
              aria-selected={value === a.mint}
              className={`calculator-asset-item probed${value === a.mint ? " selected" : ""}`}
              onClick={() => onChange(a.mint)}
            >
              <span className="calculator-asset-symbol">{a.symbol}</span>
              <span className="calculator-asset-meta">
                {a.kind}
                {a.latest_score?.grade ? ` · ${a.latest_score.grade}` : ""}
              </span>
            </button>
          ))}
        </div>
      )}
      {awaiting.length > 0 && (
        <div className="calculator-asset-group">
          <div className="calculator-asset-group-label awaiting">{dict.awaitingProbeGroup}</div>
          {awaiting.map((a) => (
            <button
              type="button"
              key={a.mint}
              role="option"
              aria-selected={value === a.mint}
              className={`calculator-asset-item awaiting${value === a.mint ? " selected" : ""}`}
              onClick={() => onChange(a.mint)}
            >
              <span className="calculator-asset-symbol">{a.symbol}</span>
              <span className="calculator-asset-meta">{a.kind}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

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
    probed_at: string;
  } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);

  const { probed, awaiting } = useMemo(() => {
    const withData = assets.filter((a) => a.is_probed);
    const queued = assets.filter((a) => !a.is_probed);
    return { probed: withData, awaiting: queued };
  }, [assets]);

  const selected = assets.find((a) => a.mint === mint);

  useEffect(() => {
    fetchAssets()
      .then((rows) => {
        setAssets(rows);
        const firstProbed = rows.find((a) => a.is_probed);
        if (firstProbed) setMint(firstProbed.mint);
      })
      .catch((e) => setLoadError(e.message));
  }, []);

  useEffect(() => {
    setError(null);
    setResult(null);
  }, [mint]);

  async function run() {
    if (!selected?.is_probed) {
      setError(dict.notProbedYet);
      return;
    }
    setError(null);
    setResult(null);
    try {
      const quote = await fetchExitQuote(mint, notional);
      setResult(quote);
    } catch (e: unknown) {
      const message = e instanceof Error ? e.message : "Unknown error";
      setError(message.includes("404") ? dict.notProbedYet : message);
    }
  }

  return (
    <div>
      <h1>{dict.calculatorTitle}</h1>
      <p className="muted">{dict.calculatorSubtitle}</p>
      <p className="muted" style={{ maxWidth: 640, marginTop: 8 }}>
        {dict.calculatorDescription}
      </p>

      <p className="muted calculator-coverage-note">
        {dict.calculatorCoverageNote
          .replace("{available}", String(probed.length))
          .replace("{total}", String(assets.length))}
      </p>

      <div className="panel calculator-form">
        <div className="calculator-field">
          <span>{dict.selectAsset}</span>
          {selected && (
            <div
              className={`calculator-selected-badge${selected.is_probed ? " probed" : " awaiting"}`}
            >
              {selected.symbol} —{" "}
              {selected.is_probed ? dict.assetProbedLabel : dict.assetAwaitingLabel}
            </div>
          )}
          <AssetPicker
            probed={probed}
            awaiting={awaiting}
            value={mint}
            onChange={setMint}
            dict={dict}
          />
          <span className="muted calculator-field-hint">{dict.selectProbedHint}</span>
        </div>

        <label className="calculator-field">
          <span>{dict.calculatorNotionalLabel}</span>
          <input
            type="number"
            min={1}
            step={1000}
            value={notional}
            onChange={(e) => setNotional(Number(e.target.value))}
          />
          <span className="muted calculator-field-hint">{dict.calculatorNotionalHint}</span>
        </label>

        <button type="button" onClick={run} disabled={!mint || !selected?.is_probed}>
          {dict.calculate}
        </button>
      </div>

      {loadError && <div className="panel">{loadError}</div>}
      {selected && !selected.is_probed && (
        <div className="panel calculator-awaiting-notice">{dict.notProbedYet}</div>
      )}
      {error && <div className="panel">{error}</div>}
      {result && (
        <div className="panel calculator-result">
          <p className="muted calculator-field-hint">
            {dict.probedAt}: {new Date(result.probed_at).toLocaleString()}
          </p>
          <p>
            {dict.requested}: ${result.notional_usd.toLocaleString()}
          </p>
          <p>
            {dict.matchedRung}: ${result.matched_notional_usd.toLocaleString()}
          </p>
          <p>
            {dict.cashOut}:{" "}
            {result.no_route ? dict.noRoute : `$${(result.cash_usd || 0).toLocaleString()}`}
          </p>
          <p>
            {dict.routeCols.route}: {result.route_labels}
          </p>
          <p>
            {dict.bindingLeg}: {result.binding_leg || "-"}
          </p>
        </div>
      )}
    </div>
  );
}
