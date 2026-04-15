const LAST_JOB_KEY = "extrace:lastJobId";

export function getStoredJobId() {
  if (typeof window === "undefined") return null;
  const storage = window.localStorage;
  return typeof storage?.getItem === "function" ? storage.getItem(LAST_JOB_KEY) : null;
}

export function rememberJobId(jobId: string) {
  if (typeof window === "undefined") return;
  const storage = window.localStorage;
  if (typeof storage?.setItem === "function") {
    storage.setItem(LAST_JOB_KEY, jobId);
  }
}
