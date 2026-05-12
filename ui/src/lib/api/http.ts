import { getApiBaseUrl } from "./runtime";

export class ApiError extends Error {
  status: number;
  /**
   * The original `detail` field from a FastAPI error response, when one
   * was present. May be a string (legacy / generic errors) or a
   * structured object (e.g. the VSIX threshold-breach 422 surfaced by
   * /api/marketplace/download). Callers that want to render specific
   * UI for a typed payload should `instanceof ApiError`-check then
   * narrow `detail` themselves.
   */
  detail?: unknown;

  constructor(message: string, status: number, detail?: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}

export async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const baseUrl = getApiBaseUrl();
  const requestUrl = baseUrl ? `${baseUrl}${path}` : path;

  const response = await fetch(requestUrl, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
  });

  if (response.status === 204) {
    return undefined as T;
  }

  if (!response.ok) {
    let message = response.statusText;
    let detail: unknown;
    const bodyText = await response.text();
    try {
      const payload = JSON.parse(bodyText);
      detail = (payload as { detail?: unknown }).detail;
      if (typeof detail === "string") {
        message = detail;
      } else if (detail !== undefined) {
        message = JSON.stringify(detail);
      } else {
        message = JSON.stringify(payload);
      }
    } catch {
      message = bodyText;
    }
    throw new ApiError(message || "Request failed", response.status, detail);
  }

  return (await response.json()) as T;
}
