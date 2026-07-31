"""DB-free API coverage for the read-only Rules whitelist surface."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_get_whitelist_returns_domains_companies_and_effect_scope(
    client: TestClient,
) -> None:
    response = client.get("/api/rules/whitelist")

    assert response.status_code == 200
    body = response.json()
    assert body["domain_count"] == len(body["domains"])
    assert body["organization_count"] == len(body["organizations"])
    assert body["extension_count"] == len(body["extension_identities"])
    assert "extrace.a1.credential_read_then_network" in body["domain_filtered_rule_ids"]

    domains = {entry["domain"]: entry for entry in body["domains"]}
    assert domains["vscode-cdn.net"]["organization"] == (
        "Microsoft / Visual Studio Code"
    )
    assert domains["registry.npmjs.org"]["organization"] == "npm"

    organizations = {entry["id"]: entry for entry in body["organizations"]}
    assert "ms-python" in organizations["microsoft-vscode"]["publishers"]
    assert "ms-python.python" in organizations["microsoft-vscode"]["extensions"]


def test_whitelist_is_read_only(client: TestClient) -> None:
    response = client.post("/api/rules/whitelist", json={"domain": "example.org"})
    assert response.status_code == 405
    assert client.delete("/api/rules/whitelist/example.org").status_code == 404
