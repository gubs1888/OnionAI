"""
POST /api/analyze schema + end-to-end DEMO pipeline flow.

In DEMO MODE the inference is deterministic per image content, so these tests
are stable without any real model.
"""

FAKE_JPG = b"\xff\xd8\xff\xe0" + b"onion-quality-ai-test-image" * 64  # bytes don't matter in DEMO


def _upload(client, batch_code=None, filename="onions.jpg"):
    data = {}
    if batch_code:
        data["batch_id"] = batch_code
    return client.post(
        "/api/analyze",
        files={"image": (filename, FAKE_JPG, "image/jpeg")},
        data=data,
    )


def test_analyze_response_schema(client):
    batch = client.post("/api/batches", json={"name": "Analysis batch"}).json()
    res = _upload(client, batch["batch_code"])
    assert res.status_code == 200, res.text
    body = res.json()

    # Backend -> Mobile contract fields (docs/api/API_CONTRACT.md)
    for field in (
        "batch_id", "total_onions", "healthy", "damaged", "rotten", "sprouted",
        "undersized", "defect_percentage", "quality_score", "grade",
        "urs_percentage", "confidence", "reasons", "is_demo", "model_version",
        "assessment_id", "image_id", "detections",
    ):
        assert field in body, f"missing contract field: {field}"

    assert body["batch_id"] == batch["batch_code"]
    assert body["is_demo"] is True                       # honesty flag
    assert body["model_version"] == "demo-v0"
    assert 0 <= body["quality_score"] <= 100
    assert body["grade"] in ("A", "B", "C", "D")
    assert body["confidence"] == round(body["confidence"], 1)

    # Buckets are mutually exclusive and sum to total
    total = body["total_onions"]
    assert total > 0
    assert (
        body["healthy"] + body["damaged"] + body["rotten"]
        + body["sprouted"] + body["undersized"] == total
    )

    # Detection items follow the ML -> Backend contract
    det = body["detections"][0]
    for field in ("class_name", "class_id", "confidence", "bbox"):
        assert field in det
    assert det["class_name"] in ("onion", "damaged", "rotten", "sprouted")
    assert len(det["bbox"]) == 4


def test_analyze_is_deterministic_per_image(client):
    r1 = _upload(client).json()
    r2 = _upload(client).json()
    assert r1["total_onions"] == r2["total_onions"]      # same bytes -> same demo result
    assert r1["healthy"] == r2["healthy"]


def test_analyze_then_get_assessment(client):
    batch = client.post("/api/batches", json={"name": "Assessed batch"}).json()
    analyzed = _upload(client, batch["batch_code"]).json()

    res = client.get(f"/api/batches/{batch['batch_code']}/assessment")
    assert res.status_code == 200
    assessment = res.json()
    assert assessment["assessment_id"] == analyzed["assessment_id"]
    assert assessment["grade"] in ("A", "B", "C", "D")


def test_analyze_unknown_batch_404(client):
    res = _upload(client, batch_code="NOPE-999")
    assert res.status_code == 404
    assert res.json()["error"]["code"] == "BATCH_NOT_FOUND"


def test_analyze_rejects_bad_extension(client):
    res = client.post(
        "/api/analyze",
        files={"image": ("malware.exe", FAKE_JPG, "application/octet-stream")},
    )
    assert res.status_code == 422
    assert res.json()["error"]["code"] == "UNSUPPORTED_FILE_TYPE"


def test_report_generation_flow(client):
    analyzed = _upload(client).json()
    created = client.post(f"/api/reports/{analyzed['assessment_id']}")
    assert created.status_code == 201, created.text
    report = created.json()
    assert report["report_code"].startswith("RPT-")
    assert report["is_demo"] is True

    fetched = client.get(f"/api/reports/{report['report_id']}")
    assert fetched.status_code == 200
    assert fetched.json()["download_url"].endswith("/download")

    pdf = client.get(f"/api/reports/{report['report_id']}/download")
    assert pdf.status_code == 200
    assert pdf.headers["content-type"] == "application/pdf"
    assert pdf.content[:5] == b"%PDF-"
