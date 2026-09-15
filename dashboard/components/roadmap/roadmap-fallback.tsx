import { resolveStageStatus, type RoadmapLegend, type RoadmapStage } from "./types";

type Props = {
  stages: RoadmapStage[];
  legend: RoadmapLegend;
};

export function RoadmapFallback({ stages, legend }: Props) {
  const n = stages.length;

  return (
    <div className="roadmap-fallback" role="img" aria-label="Roadmap timeline">
      <svg viewBox="0 0 400 80" className="roadmap-fallback__svg" preserveAspectRatio="xMidYMid meet">
        <line x1="40" y1="40" x2="360" y2="40" className="roadmap-fallback__line" />
        {stages.map((stage, index) => {
          const status = resolveStageStatus(stage);
          const cx = 40 + (n > 1 ? index * (320 / (n - 1)) : 0);
          return (
            <g key={stage.id}>
              <circle
                cx={cx}
                cy={40}
                r={8}
                className={`roadmap-fallback__node roadmap-fallback__node--${status}`}
              />
              <text x={cx} y={64} textAnchor="middle" className="roadmap-fallback__label">
                {stage.shortLabel}
              </text>
            </g>
          );
        })}
      </svg>
      <div className="roadmap-legend">
        <span className="roadmap-legend__item roadmap-legend__item--complete">{legend.complete}</span>
        <span className="roadmap-legend__item roadmap-legend__item--active">{legend.active}</span>
        <span className="roadmap-legend__item roadmap-legend__item--planned">{legend.planned}</span>
      </div>
    </div>
  );
}
