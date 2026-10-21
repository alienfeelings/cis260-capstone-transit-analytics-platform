import json
from ingestion.realtime import predictions
# python -m pytest -v runs all tests

class FakeResponse:

    def raise_for_status(self):
        pass

    def json(self):
        return {
            "data": [
                {
                    "id": "prediction-test-1"
                },
                {
                    "id": "prediction-test-2"
                }
            ]
        }

def fake_get(url, params, headers, timeout):
    assert url == predictions.url
    assert params == predictions.my_params
    assert headers == predictions.my_headers
    assert timeout == 30

    return FakeResponse()

def test_collect_predictions_saves_snapshot(tmp_path, monkeypatch):

    monkeypatch.setattr(
        predictions,
        "PROJECT_ROOT",
        tmp_path
    )

    monkeypatch.setattr(
        predictions.requests,
        "get",
        fake_get
    )

    filename = predictions.collect_predictions()

    assert filename is not None
    assert filename.exists()
    assert filename.parent == (
        tmp_path / "data" / "raw" / "predictions"
    )

    with open(filename, "r", encoding="utf-8") as file:
        saved_data = json.load(file)

    assert len(saved_data["data"]) == 2
    assert (
        saved_data["data"][0]["id"]
        == "prediction-test-1"
    )

def test_collect_predictions_handles_api_failure(monkeypatch, caplog):

    def fake_failed_get(
        url,
        params,
        headers,
        timeout
    ):
        raise predictions.requests.RequestException(
            "Test prediction API failure"
        )

    monkeypatch.setattr(
        predictions.requests,
        "get",
        fake_failed_get
    )

    result =  predictions.collect_predictions()

    assert result is None
    assert (
        "Prediction API request failed"
        in caplog.text
    )