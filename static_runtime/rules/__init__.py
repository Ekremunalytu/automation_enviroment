"""In-house static rules (ADR 0016 static pre-check).

Production rules span manifest red flags, typosquat/file-tree heuristics,
network and IOC indicators, obfuscation/secrets, reverse shells, download
cradles, and GlassWorm-style Unicode/native-loader/dormancy signals.
Mirrors the dynamic
``packages.analysis_engine.rules`` package shape (base Protocol + self-
registering rule singletons + a lazy registry) but lives under
``static_runtime`` so the hardened image carries it without the dynamic engine.
"""
