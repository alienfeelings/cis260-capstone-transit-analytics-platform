import json
from ingestion.realtime import vehicles
# python -m pytest -v runs all tests

class FakeResponse:

    def raise_for_status(self):
        pass

    def json(self):
        return {
            "data": [
                {
                    "id": "vehicle-test-1"
                }
            ]
        }

def fake_get(url, params, headers, timeout):
    assert url == vehicles.url
    assert params == vehicles.my_params
    assert headers == vehicles.my_headers
    assert timeout == 30

    return FakeResponse()

def test_collect_vehicles_saves_snapshot(tmp_path, monkeypatch):
    # Replace the real project directory with
    # pytest's temporary directory.
    monkeypatch.setattr(
        vehicles,
        "PROJECT_ROOT",
        tmp_path
    )

    # Replace the real requests.get() call
    # with our fake version.
    monkeypatch.setattr(
        vehicles.requests,
        "get",
        fake_get
    )

    filename = vehicles.collect_vehicles()

    assert filename is not None
    assert filename.exists()
    assert filename.parent == (
        tmp_path / "data" / "raw" / "vehicles"
    )

    with open(filename, "r", encoding="utf-8") as file:
        saved_data = json.load(file)

    assert len(saved_data["data"]) == 1
    assert (saved_data["data"][0]["id"] == "vehicle-test-1")

def test_collect_vehicles_handles_api_failure(monkeypatch, caplog):

    def fake_failed_get(
        url,
        params,
        headers,
        timeout
    ):
        raise vehicles.requests.RequestException(
            "Test API failure"
        )

    monkeypatch.setattr(
        vehicles.requests,
        "get",
        fake_failed_get
    )

    result = vehicles.collect_vehicles()

    assert result is None

    assert (
        "Vehicle API request failed"
        in caplog.text
    )