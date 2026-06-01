# Static analysis pre-check container (ES-2, ADR 0016 §Decision 2).
#
# Hardened, minimal image that (from ES-3a) parses untrusted VSIX manifests and
# file trees off the host and off the executor. Reuses the api image's audited
# python:3.11-slim-bookworm base digest rather than introducing a second base
# image to audit; 3.11 is sufficient for the pydantic-only runtime stub. The
# container is driven from the host via `docker exec` (executor/static_host.py)
# and idles under the compose `command` so exec always has a live target.
#
# Base digest pinned per ADR 0002 §4 trust boundary
# (tests/architecture/test_dockerfile_digest_pin.py).
FROM python:3.11-slim-bookworm@sha256:cd67330292a51e2963156f74ff340455d66b2172e9190e99f40dff9357471177

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Non-root user. The container starts directly AS this user (no gosu/nginx-style
# runtime privilege drop), so it needs no SETUID/SETGID caps — unlike api/ui.
RUN useradd -m -u 10001 static

WORKDIR /app

# Dependency layer first for build caching.
COPY docker/static_analyzer/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Minimal application surface: the pydantic-only static-detection contracts and
# the runtime stub. Deliberately NOT packages/analysis_engine (the dynamic
# detection engine) — importing that here would drag the whole engine into the
# hardened image. See static_runtime/__init__.py for the rationale.
COPY packages/__init__.py ./packages/__init__.py
COPY packages/analysis_contracts/ ./packages/analysis_contracts/
COPY static_runtime/ ./static_runtime/

# IPC mount points: read-only extensions input, read-write results (mounts are
# overlaid by the compose volumes at runtime).
RUN mkdir -p /extensions-input /results

USER static

# One-shot analyzer driven by `docker exec`; this CMD only documents usage and
# is overridden by the compose `command: ["sleep", "infinity"]` that keeps the
# container alive so exec has a target.
CMD ["python", "-m", "static_runtime", "--help"]
