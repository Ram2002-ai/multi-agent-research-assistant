from __future__ import annotations

import time


def wait_for_report(client, job_id: str) -> dict:
    for _ in range(100):
        response = client.get(f"/api/v1/research/{job_id}")
        assert response.status_code == 200
        report = response.json()
        if report["status"] in {"completed", "failed"}:
            return report
        time.sleep(0.01)
    raise AssertionError("Research job did not reach a terminal state")


def test_health_and_compatibility_metadata(client):
    assert client.get("/health").json()["status"] == "ok"
    assert client.get("/debug_model").json()["model"].startswith("openrouter/")
    assert client.get("/openapi.json").status_code == 200


def test_live_research_persists_events_sources_and_memory(client):
    response = client.post(
        "/api/v1/research",
        json={"topic": "How does satellite climate monitoring work?"},
    )
    assert response.status_code == 202
    job_id = response.json()["job_id"]
    report = wait_for_report(client, job_id)
    assert report["status"] == "completed"
    assert report["progress"] == 100

    detail = client.get(f"/api/v1/reports/{job_id}").json()
    assert len(detail["events"]) >= 14
    assert detail["sources"][0]["label"] in {"Highly Trusted", "Trusted"}
    assert detail["citations"]["ieee"]
    assert detail["graph"]["nodes"]
    assert "flowchart" in detail["diagrams"]["pipeline"]

    memory = client.post(
        "/api/v1/knowledge/search", json={"query": "NASA satellite evidence"}
    ).json()
    assert memory["count"] >= 1
    assert memory["items"][0]["report_id"] == job_id


def test_sse_replays_completed_timeline_and_closes(client):
    started = client.post("/api/v1/research", json={"topic": "Test event replay"}).json()
    wait_for_report(client, started["job_id"])
    with client.stream("GET", started["stream_url"]) as response:
        content = "".join(response.iter_text())
    assert response.status_code == 200
    assert "event: agent" in content
    assert '"status": "completed"' in content


def test_exports_history_and_analytics(client):
    started = client.post("/api/v1/research", json={"topic": "Export test"}).json()
    job_id = started["job_id"]
    wait_for_report(client, job_id)

    for format_name in ("md", "html", "json", "csv", "docx", "zip"):
        response = client.get(f"/api/v1/reports/{job_id}/export/{format_name}")
        assert response.status_code == 200
        assert response.content

    reports = client.get("/api/v1/reports").json()
    assert reports["count"] == 1
    analytics = client.get("/api/v1/analytics").json()
    assert analytics["total_reports"] == 1
    assert analytics["success_rate"] == 100


def test_registration_login_and_user_configuration(client):
    payload = {
        "email": "researcher@example.com",
        "name": "Researcher",
        "password": "a-secure-password",
    }
    registration = client.post("/api/v1/auth/register", json=payload)
    assert registration.status_code == 200
    token = registration.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    assert client.get("/api/v1/auth/me", headers=headers).status_code == 200

    login = client.post(
        "/api/v1/auth/login",
        json={"email": payload["email"], "password": payload["password"]},
    )
    assert login.status_code == 200

    config = client.get("/api/v1/config", headers=headers).json()
    config["temperature"] = 0.6
    saved = client.put("/api/v1/config", headers=headers, json=config)
    assert saved.status_code == 200
    assert saved.json()["temperature"] == 0.6
