# ExTrace T1 Runnable Demo Canary

This is a safe, runnable malicious-behavior simulation for local ExTrace demos.
It is a T1 internal canary, not a real malicious extension.

What it does when the command runs:

- writes and reads `.extrace-demo/secrets.env` inside the open workspace;
- shows a visible simulated credential prompt warning;
- attempts one short POST to `127.0.0.1:8787/extrace-demo`;
- emits `EXTRACE_DEMO_EVENT` JSON lines to the `ExTrace Demo Canary` output channel.

What it does not do:

- it does not read real credential files;
- it does not contact external hosts;
- it does not execute shell commands;
- it does not run until `ExTrace Demo: Run Safe Malicious Simulation` is invoked.

The adjacent `activation_report.json` is an offline detection fixture that
exercises A1, A4, and A6 rules with synthetic evidence. The runnable extension
stays declawed and uses localhost-only network behavior.
