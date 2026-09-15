export type RoadmapStageStatus = "complete" | "active" | "planned";

export type RoadmapStage = {
  id: string;
  status?: RoadmapStageStatus | string;
  shortLabel: string;
  title: string;
  items: string[];
};

export type RoadmapLegend = {
  complete: string;
  active: string;
  planned: string;
};

const STATUS_BY_ID: Record<string, RoadmapStageStatus> = {
  shipped: "complete",
  "solana-next": "active",
};

export function resolveStageStatus(stage: RoadmapStage): RoadmapStageStatus {
  if (stage.status === "complete" || stage.status === "active" || stage.status === "planned") {
    return stage.status;
  }
  return STATUS_BY_ID[stage.id] ?? "planned";
}

export function stagePosition(index: number): [number, number, number] {
  const x = index * 3.4 - 5.1;
  const y = index * 1.15;
  const z = index * -1.9 + 0.5;
  return [x, y, z];
}

export function monolithHeight(index: number): number {
  return 0.95 + index * 0.55;
}
