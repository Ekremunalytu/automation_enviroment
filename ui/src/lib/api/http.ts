import { getApiBaseUrl } from "./runtime";

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
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
    try {
      const payload = await response.json();
      message = typeof payload.detail === "string" ? payload.detail : JSON.stringify(payload);
    } catch {
      message = await response.text();
    }
    throw new ApiError(message || "Request failed", response.status);
  }

  return (await response.json()) as T;
}
