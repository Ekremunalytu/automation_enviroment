import { useMemo } from "react";

import { RISK_COLOR, V3, type Risk } from "../../../components/v3";

export type InteractionGroupChild = {
  id: string;
  label: string;
  count: number;
  meta?: string;
  risk?: Risk;
};

export type InteractionGroup = {
  id: string;
  label: string;
  count: number;
  pct?: number;
  axis: "network" | "fs" | "activation" | "secret" | "process";
  description?: string;
  children: InteractionGroupChild[];
};

export type InteractionGraphData = {
  rootLabel: string;
  rootMeta?: string;
  groups: InteractionGroup[];
};

type InteractionGraphProps = {
  data: InteractionGraphData;
  height?: number;
};

const COLUMN_X = { root: 60, category: 360, leaf: 760 };
const ROOT_DIM = { width: 200, height: 80 };
const CATEGORY_DIM = { width: 240, height: 64 };
const LEAF_DIM = { width: 180, height: 48 };
const MIN_LEAF_SPACING = 58;
const LEAF_CAP = 6;

export function InteractionGraph({ data, height = 480 }: InteractionGraphProps) {
  const layout = useMemo(() => {
    const groups = data.groups.slice(0, 5).map((group) => {
      const childCount = group.children.length;
      const visible = group.children.slice(0, LEAF_CAP);
      const overflow = childCount - visible.length;
      if (overflow > 0 && visible.length > 0) {
        const last = visible[visible.length - 1];
        return {
          ...group,
          children: [
            ...visible.slice(0, -1),
            {
              ...last,
              meta: `+${overflow} more${last.meta ? ` · ${last.meta}` : ""}`,
            },
          ],
        };
      }
      return { ...group, children: visible };
    });
    const totalLeaves = groups.reduce((acc, group) => acc + Math.max(1, group.children.length), 0);
    const minHeight = totalLeaves * MIN_LEAF_SPACING + 40;
    const computedHeight = Math.max(height, minHeight);
    const verticalUnit = Math.max(
      (computedHeight - 40) / Math.max(totalLeaves, 1),
      MIN_LEAF_SPACING,
    );

    type PositionedChild = InteractionGroupChild & { x: number; y: number };
    type PositionedGroup = Omit<InteractionGroup, "children"> & {
      index: number;
      center: number;
      children: PositionedChild[];
    };

    const positionedGroups = groups.reduce<{ cursor: number; groups: PositionedGroup[] }>(
      (acc, group, groupIndex) => {
        const groupHeight = Math.max(1, group.children.length) * verticalUnit;
        const groupTop = acc.cursor;
        const groupCenter = groupTop + groupHeight / 2;
        const positionedChildren: PositionedChild[] = group.children.map((child, childIndex) => ({
          ...child,
          x: COLUMN_X.leaf,
          y: groupTop + (childIndex + 0.5) * verticalUnit,
        }));
        acc.groups.push({
          ...group,
          index: groupIndex,
          center: groupCenter,
          children: positionedChildren,
        });
        acc.cursor = groupTop + groupHeight;
        return acc;
      },
      { cursor: 20, groups: [] },
    ).groups;

    return {
      groups: positionedGroups,
      width: 980,
      height: computedHeight,
      rootCenter: computedHeight / 2,
    };
  }, [data, height]);

  return (
    <svg
      role="img"
      aria-label="Interaction flow graph"
      viewBox={`0 0 ${layout.width} ${layout.height}`}
      style={{ width: "100%", height: "auto", display: "block" }}
    >
      <rect
        x={COLUMN_X.root}
        y={layout.rootCenter - ROOT_DIM.height / 2}
        width={ROOT_DIM.width}
        height={ROOT_DIM.height}
        fill={V3.paper3}
        stroke={V3.coral}
        strokeWidth={1.5}
      />
      <text
        x={COLUMN_X.root + ROOT_DIM.width / 2}
        y={layout.rootCenter - 6}
        textAnchor="middle"
        fontFamily="'Manrope', sans-serif"
        fontSize={14}
        fontWeight={700}
        fill={V3.ink}
        letterSpacing="0"
      >
        {data.rootLabel}
      </text>
      {data.rootMeta ? (
        <text
          x={COLUMN_X.root + ROOT_DIM.width / 2}
          y={layout.rootCenter + 14}
          textAnchor="middle"
          fontFamily="'JetBrains Mono', monospace"
          fontSize={10}
          fill={V3.ink3}
          letterSpacing="0.12em"
        >
          {data.rootMeta.toUpperCase()}
        </text>
      ) : null}

      {layout.groups.map((group) => {
        const groupX = COLUMN_X.category;
        const groupY = group.center - CATEGORY_DIM.height / 2;
        return (
          <g key={group.id}>
            <path
              d={curve(
                COLUMN_X.root + ROOT_DIM.width,
                layout.rootCenter,
                groupX,
                group.center,
              )}
              fill="none"
              stroke={V3.rule2}
              strokeWidth={1.5}
              strokeDasharray="6 6"
              className="animate-flowDash"
            />
            <rect
              x={groupX}
              y={groupY}
              width={CATEGORY_DIM.width}
              height={CATEGORY_DIM.height}
              fill={V3.paper2}
              stroke={V3.rule}
              strokeWidth={1}
            />
            <text
              x={groupX + 12}
              y={groupY + 22}
              fontFamily="'Manrope', sans-serif"
              fontSize={13}
              fontWeight={700}
              fill={V3.ink}
              letterSpacing="0"
            >
              {group.label}
            </text>
            <text
              x={groupX + 12}
              y={groupY + 42}
              fontFamily="'JetBrains Mono', monospace"
              fontSize={10}
              fill={V3.ink3}
              letterSpacing="0.1em"
            >
              {group.count} EVENTS
              {typeof group.pct === "number" ? ` · ${group.pct}%` : ""}
            </text>

            {group.children.map((child) => {
              const fill = RISK_COLOR[child.risk ?? "low"];
              return (
                <g key={child.id}>
                  <path
                    d={curve(groupX + CATEGORY_DIM.width, group.center, child.x, child.y)}
                    fill="none"
                    stroke={fill}
                    strokeOpacity={0.5}
                    strokeWidth={1.2}
                    strokeDasharray="4 6"
                    className="animate-flowDashFast"
                  />
                  <rect
                    x={child.x}
                    y={child.y - LEAF_DIM.height / 2}
                    width={LEAF_DIM.width}
                    height={LEAF_DIM.height}
                    fill={V3.paper2}
                    stroke={V3.rule}
                    strokeWidth={1}
                  />
                  <text
                    x={child.x + 10}
                    y={child.y - 2}
                    fontFamily="'JetBrains Mono', monospace"
                    fontSize={11}
                    fontWeight={500}
                    fill={V3.ink}
                  >
                    {truncate(child.label, 22)}
                  </text>
                  <text
                    x={child.x + 10}
                    y={child.y + 14}
                    fontFamily="'JetBrains Mono', monospace"
                    fontSize={10}
                    fill={V3.ink3}
                    letterSpacing="0.06em"
                  >
                    {child.meta ?? `${child.count}×`}
                  </text>
                  <rect
                    x={child.x + LEAF_DIM.width - 14}
                    y={child.y - LEAF_DIM.height / 2 + 6}
                    width={6}
                    height={6}
                    fill={fill}
                  />
                </g>
              );
            })}
          </g>
        );
      })}
    </svg>
  );
}

function curve(x1: number, y1: number, x2: number, y2: number): string {
  const midX = x1 + (x2 - x1) / 2;
  return `M ${x1} ${y1} C ${midX} ${y1}, ${midX} ${y2}, ${x2} ${y2}`;
}

function truncate(value: string, max: number): string {
  if (value.length <= max) return value;
  return `${value.slice(0, max - 1)}…`;
}
