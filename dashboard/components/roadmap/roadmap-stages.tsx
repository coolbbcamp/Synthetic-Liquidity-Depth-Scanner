import { resolveStageStatus, type RoadmapStage } from "./types";

type Props = {
  stages: RoadmapStage[];
};

export function RoadmapStages({ stages }: Props) {
  return (
    <div className="roadmap-timeline prose">
      {stages.map((stage) => {
        const status = resolveStageStatus(stage);
        return (
          <section key={stage.id} className={`roadmap-stage roadmap-stage--${status}`}>
            <div className="roadmap-timeline__rail" aria-hidden="true">
              <span className={`roadmap-timeline__node roadmap-timeline__node--${status}`} />
            </div>
            <div className="roadmap-stage__content">
              <h2>{stage.title}</h2>
              <ul>
                {stage.items.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
          </section>
        );
      })}
    </div>
  );
}
