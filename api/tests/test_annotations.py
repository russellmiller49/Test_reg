from datetime import date

from fastapi.testclient import TestClient


def test_create_and_fetch_annotation(client: TestClient):
    payload = {
        "date": date.today().isoformat(),
        "operators": ["Dr. Smith", "Dr. Jones"],
        "sedation": "GA",
        "complications": "None",
        "notes": "Procedure uneventful.",
        "procedure_type": "EBUS",
        "procedure_details": {
            "nodeStations": ["4R", "7"],
            "needleGauge": "22G",
            "totalPasses": 4,
            "rosePerformed": True,
            "adequacy": "Adequate",
        },
    }

    create_response = client.post("/api/annotations", json=payload)
    assert create_response.status_code == 201, create_response.text
    created = create_response.json()
    assert created["procedure_type"] == "EBUS"
    assert created["procedure_details"]["nodeStations"] == ["4R", "7"]
    annotation_id = created["id"]

    get_response = client.get(f"/api/annotations/{annotation_id}")
    assert get_response.status_code == 200
    fetched = get_response.json()
    assert fetched["id"] == annotation_id
    assert fetched["operators"] == payload["operators"]

    list_response = client.get("/api/annotations")
    assert list_response.status_code == 200
    items = list_response.json()
    assert any(item["id"] == annotation_id for item in items)
