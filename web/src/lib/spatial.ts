import type { SpatialExtent } from "./api";
import type { TypeThemeKey } from "./typeTheme";

export interface ViewBounds {
  south: number;
  west: number;
  north: number;
  east: number;
  isPoint: boolean;
}

const VIEW_WIDTH = 36;
const VIEW_HEIGHT = 20;

export function unionBounds(spatial: SpatialExtent): ViewBounds | null {
  const boxes = [
    ...spatial.boxes.map((box) => ({
      south: box.south,
      west: box.west,
      north: box.north,
      east: box.east,
    })),
    ...spatial.points.map((point) => ({
      south: point.lat,
      west: point.lon,
      north: point.lat,
      east: point.lon,
    })),
  ];

  if (!boxes.length) return null;

  return {
    south: Math.min(...boxes.map((box) => box.south)),
    west: Math.min(...boxes.map((box) => box.west)),
    north: Math.max(...boxes.map((box) => box.north)),
    east: Math.max(...boxes.map((box) => box.east)),
    isPoint: spatial.points.length > 0 && spatial.boxes.length === 0 && spatial.points.length === 1,
  };
}

export function lonToX(lon: number): number {
  return ((lon + 180) / 360) * VIEW_WIDTH;
}

export function latToY(lat: number): number {
  return ((90 - lat) / 180) * VIEW_HEIGHT;
}

export function boundsToSvg(bounds: ViewBounds): {
  x: number;
  y: number;
  width: number;
  height: number;
  isPoint: boolean;
} {
  const x1 = lonToX(bounds.west);
  const x2 = lonToX(bounds.east);
  const y1 = latToY(bounds.north);
  const y2 = latToY(bounds.south);

  if (bounds.isPoint || (bounds.south === bounds.north && bounds.west === bounds.east)) {
    return {
      x: (x1 + x2) / 2,
      y: (y1 + y2) / 2,
      width: 0,
      height: 0,
      isPoint: true,
    };
  }

  let x = Math.min(x1, x2);
  let y = Math.min(y1, y2);
  let width = Math.abs(x2 - x1);
  let height = Math.abs(y2 - y1);

  const minSize = 1.2;
  if (width < minSize) {
    x -= (minSize - width) / 2;
    width = minSize;
  }
  if (height < minSize) {
    y -= (minSize - height) / 2;
    height = minSize;
  }

  return { x, y, width, height, isPoint: false };
}

function formatCoord(value: number, isLat: boolean): string {
  const rounded = Math.round(Math.abs(value) * 10) / 10;
  const suffix = isLat ? (value >= 0 ? "N" : "S") : value >= 0 ? "E" : "W";
  return `${rounded}°${suffix}`;
}

export function formatExtentLabel(bounds: ViewBounds): string {
  if (bounds.isPoint || (bounds.south === bounds.north && bounds.west === bounds.east)) {
    return `${formatCoord(bounds.south, true)}, ${formatCoord(bounds.west, false)}`;
  }

  const lat =
    bounds.south === bounds.north
      ? formatCoord(bounds.south, true)
      : `${formatCoord(bounds.south, true)}–${formatCoord(bounds.north, true)}`;

  if (Math.abs(bounds.east - bounds.west) < 0.001) {
    return lat;
  }

  const lon = `${formatCoord(bounds.west, false)}–${formatCoord(bounds.east, false)}`;
  return `${lat}, ${lon}`;
}

export const extentThemeClass: Record<TypeThemeKey, string> = {
  dataset: "dataset",
  literature: "literature",
  org: "org",
  training: "training",
  project: "project",
  default: "default",
};
