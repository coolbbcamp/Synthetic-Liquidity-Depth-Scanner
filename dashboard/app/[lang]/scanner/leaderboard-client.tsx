"use client";

import { useEffect, useMemo, useState } from "react";
import type { Dictionary } from "@/i18n/get-dictionary";
import { Asset, fetchAssets, Score } from "@/lib/api";

type Props = {
  dict: Dictionary["scanner"];
  common: Dictionary["common"];
  locale: string;
};

type KindFilter = "all" | "xstock" | "launch";
type TierFilter = "all" | "A" | "B" | "C";
type GradeFilter = "all" | "A" | "B" | "C" | "D" | "F";
type StatusFilter = "all" | "probed" | "awaiting";
type SortKey =
  | "mcap_exit_ratio"
  | "exit_capacity_95"
  | "exit_capacity_99"
  | "symbol"
  | "grade"
  | "probed_at";

const GRADE_ORDER: Record<string, number> = { A: 0, B: 1, C: 2, D: 3, F: 4 };

function fmtUsd(value: number | null | undefined): string {
  if (value == null) return "—";
  return `$${Math.round(value).toLocaleString()}`;
}

function fmtRatio(value: number | null | undefined): string {
  if (value == null) return "—";
  return value.toFixed(1);
}

function fmtRfq(value: number | null | undefined): string {
  if (value == null) return "—";
  return `${(value * 100).toFixed(0)}%`;
}

function fmtDate(value: string | null | undefined, locale: string): string {
  if (!value) return "—";
  return new Date(value).toLocaleString(locale);
}

export function LeaderboardClient({ dict, common, locale }: Props) {
  const [assets, setAssets] = useState<Asset[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [kindFilter, setKindFilter] = useState<KindFilter>("all");
  const [tierFilter, setTierFilter] = useState<TierFilter>("all");
  const [gradeFilter, setGradeFilter] = useState<GradeFilter>("all");
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");
  const [sortKey, setSortKey] = useState<SortKey>("mcap_exit_ratio");

  useEffect(() => {
    fetchAssets()
      .then(setAssets)
      .catch((e) => setError(e.message));
  }, []);

  const probedCount = useMemo(() => assets.filter((a) => a.is_probed).length, [assets]);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    let rows = assets.filter((asset) => {
      if (kindFilter !== "all" && asset.kind !== kindFilter) return false;
      if (tierFilter !== "all" && asset.tier !== tierFilter) return false;
      if (statusFilter === "probed" && !asset.is_probed) return false;
      if (statusFilter === "awaiting" && asset.is_probed) return false;
      if (gradeFilter !== "all") {
        const g = asset.latest_score?.grade;
        if (!g || g !== gradeFilter) return false;
      }
      if (!q) return true;
      return (
        asset.symbol.toLowerCase().includes(q) ||
        asset.name.toLowerCase().includes(q) ||
        asset.mint.toLowerCase().includes(q)
      );
    });

    rows = [...rows].sort((a, b) => {
      if (a.is_probed !== b.is_probed) return a.is_probed ? -1 : 1;

      const scoreA = a.latest_score;
      const scoreB = b.latest_score;

      if (sortKey === "symbol") {
        return a.symbol.localeCompare(b.symbol);
      }
      if (sortKey === "grade") {
        const ga = GRADE_ORDER[scoreA?.grade || "F"] ?? 9;
        const gb = GRADE_ORDER[scoreB?.grade || "F"] ?? 9;
        return ga - gb;
      }
      if (sortKey === "probed_at") {
        const ta = a.probed_at ? new Date(a.probed_at).getTime() : 0;
        const tb = b.probed_at ? new Date(b.probed_at).getTime() : 0;
        return tb - ta;
      }
      const numKey = sortKey as keyof Score;
      const va = (scoreA?.[numKey] as number | null | undefined) ?? -1;
      const vb = (scoreB?.[numKey] as number | null | undefined) ?? -1;
      return vb - va;
    });

    return rows;
  }, [assets, query, kindFilter, tierFilter, gradeFilter, statusFilter, sortKey]);

  const prefix = `/${locale}/scanner`;

  return (
    <div className="leaderboard-page">
      <h1>{dict.leaderboardTitle}</h1>
      <p className="muted">{dict.leaderboardSubtitle}</p>
      <p className="muted leaderboard-coverage-note">
        {dict.leaderboardCoverageNote
          .replace("{available}", String(probedCount))
          .replace("{total}", String(assets.length))}
      </p>

      <div className="leaderboard-toolbar panel">
        <div className="leaderboard-search-row">
          <input
            type="search"
            className="leaderboard-search"
            placeholder={dict.leaderboardSearchPlaceholder}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            aria-label={dict.leaderboardSearchPlaceholder}
          />
          <span className="leaderboard-result-count muted">
            {dict.leaderboardShowing
              .replace("{shown}", String(filtered.length))
              .replace("{total}", String(assets.length))}
          </span>
        </div>

        <div className="leaderboard-filters">
          <label className="leaderboard-filter">
            <span>{dict.filters.status}</span>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value as StatusFilter)}
            >
              <option value="all">{dict.filters.all}</option>
              <option value="probed">{dict.filters.probedOnly}</option>
              <option value="awaiting">{dict.filters.awaitingOnly}</option>
            </select>
          </label>
          <label className="leaderboard-filter">
            <span>{dict.filters.kind}</span>
            <select
              value={kindFilter}
              onChange={(e) => setKindFilter(e.target.value as KindFilter)}
            >
              <option value="all">{dict.filters.all}</option>
              <option value="xstock">{dict.filters.xstock}</option>
              <option value="launch">{dict.filters.launch}</option>
            </select>
          </label>
          <label className="leaderboard-filter">
            <span>{dict.filters.tier}</span>
            <select
              value={tierFilter}
              onChange={(e) => setTierFilter(e.target.value as TierFilter)}
            >
              <option value="all">{dict.filters.all}</option>
              <option value="A">A</option>
              <option value="B">B</option>
              <option value="C">C</option>
            </select>
          </label>
          <label className="leaderboard-filter">
            <span>{dict.filters.grade}</span>
            <select
              value={gradeFilter}
              onChange={(e) => setGradeFilter(e.target.value as GradeFilter)}
            >
              <option value="all">{dict.filters.all}</option>
              <option value="A">A</option>
              <option value="B">B</option>
              <option value="C">C</option>
              <option value="D">D</option>
              <option value="F">F</option>
            </select>
          </label>
          <label className="leaderboard-filter">
            <span>{dict.filters.sortBy}</span>
            <select value={sortKey} onChange={(e) => setSortKey(e.target.value as SortKey)}>
              <option value="mcap_exit_ratio">{dict.filters.sortMcapExit}</option>
              <option value="exit_capacity_95">{dict.filters.sortExit95}</option>
              <option value="exit_capacity_99">{dict.filters.sortExit99}</option>
              <option value="symbol">{dict.filters.sortSymbol}</option>
              <option value="grade">{dict.filters.sortGrade}</option>
              <option value="probed_at">{dict.filters.sortProbedAt}</option>
            </select>
          </label>
        </div>
      </div>

      {error && (
        <div className="panel">
          {common.apiUnavailable}: {error}
        </div>
      )}

      <div className="leaderboard-table-wrap panel">
        <table className="leaderboard-table">
          <thead>
            <tr>
              <th>{dict.columns.symbol}</th>
              <th>{dict.columns.kind}</th>
              <th>{dict.columns.tier}</th>
              <th>{dict.columns.grade}</th>
              <th>{dict.columns.exit99}</th>
              <th>{dict.columns.exit95}</th>
              <th>{dict.columns.exit90}</th>
              <th>{dict.columns.mcapExit}</th>
              <th>{dict.columns.cliff}</th>
              <th>{dict.columns.noRoute}</th>
              <th>{dict.columns.bindingLeg}</th>
              <th>{dict.columns.rfq}</th>
              <th>{dict.columns.probedAt}</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((asset) => {
              const score = asset.latest_score;
              const rowClass = asset.is_probed
                ? "leaderboard-row-probed"
                : "leaderboard-row-awaiting";

              return (
                <tr key={asset.mint} className={rowClass}>
                  <td>
                    {asset.is_probed ? (
                      <a
                        href={`${prefix}/asset/${asset.mint}`}
                        className="leaderboard-symbol-link"
                        title={asset.mint}
                      >
                        {asset.symbol}
                      </a>
                    ) : (
                      <span className="leaderboard-symbol-muted" title={asset.mint}>
                        {asset.symbol}
                      </span>
                    )}
                  </td>
                  <td>{asset.kind}</td>
                  <td>{asset.tier}</td>
                  <td className={`grade-${score?.grade || "D"}`}>{score?.grade || "—"}</td>
                  <td>{fmtUsd(score?.exit_capacity_99)}</td>
                  <td>{fmtUsd(score?.exit_capacity_95)}</td>
                  <td>{fmtUsd(score?.exit_capacity_90)}</td>
                  <td>{fmtRatio(score?.mcap_exit_ratio)}</td>
                  <td>
                    {score?.cliff_detected ? (
                      <>
                        {common.yes}
                        {score.cliff_notional != null
                          ? ` @ ${fmtUsd(score.cliff_notional)}`
                          : ""}
                      </>
                    ) : asset.is_probed ? (
                      common.no
                    ) : (
                      "—"
                    )}
                  </td>
                  <td>{fmtUsd(score?.no_route_ceiling)}</td>
                  <td>{score?.binding_leg || "—"}</td>
                  <td>{fmtRfq(score?.rfq_dependence)}</td>
                  <td className="leaderboard-probed-cell">
                    {asset.is_probed ? (
                      fmtDate(asset.probed_at, locale)
                    ) : (
                      <span className="leaderboard-queued-badge">{dict.assetAwaitingLabel}</span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
        {filtered.length === 0 && (
          <p className="muted leaderboard-empty">{dict.leaderboardNoResults}</p>
        )}
      </div>
    </div>
  );
}
