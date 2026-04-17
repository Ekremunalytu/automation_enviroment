export function getApiBaseUrl() {
  const envBaseUrl = import.meta.env.VITE_API_BASE_URL?.trim();
  if (envBaseUrl) {
    return envBaseUrl;
  }
  return window.__EXTRACE_CONFIG__?.API_BASE_URL || "";
}
