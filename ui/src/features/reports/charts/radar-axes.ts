export const RADAR_AXES = ["Threat", "Exfil", "Persistence", "Privesc", "Defense", "Resource"] as const;
export type RadarAxis = (typeof RADAR_AXES)[number];

export type RadarScore = Record<RadarAxis, number> & { _synthetic?: boolean };
