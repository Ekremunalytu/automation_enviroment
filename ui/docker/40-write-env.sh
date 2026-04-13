#!/bin/sh
set -eu

cat > /usr/share/nginx/html/env.js <<EOF
window.__EXTRACE_CONFIG__ = {
  API_BASE_URL: "${API_BASE_URL:-}",
};
EOF
