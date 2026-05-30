"""In-house static rules (ES-3a, ADR 0016 §Decision 4 MVP).

Six production rules across three namespaces (s1 manifest red flags, s2
typosquat, s3 file-tree heuristics). Mirrors the dynamic
``packages.analysis_engine.rules`` package shape (base Protocol + self-
registering rule singletons + a lazy registry) but lives under
``static_runtime`` so the hardened image carries it without the dynamic engine.
"""
