import json
from ingestion.realtime import alerts
# python -m pytest -v runs all tests

class FakeResponse:

    def raise_for_status(self):
        pass

    def json(self):
        return {
            "data": [
                {
                    "id": "alert-test-1"
                }
            ]
        }


def fake_get(url, params, headers, timeout):

    assert url == alerts.url
    assert params == alerts.my_params
    assert headers == alerts.my_headers
    assert timeout == 30

    return FakeResponse()


def test_collect_alerts_saves_snapshot(
        tmp_path,
        monkeypatch
):

    monkeypatch.setattr(
        alerts,
        "PROJECT_ROOT",
        tmp_path
    )

    monkeypatch.setattr(
        alerts.requests,
        "get",
        fake_get
    )

    filename = alerts.collect_alerts()

    assert filename is not None

    assert filename.exists()

    assert filename.parent == (
        tmp_path / "data" / "raw" / "alerts"
    )

    with open(
        filename,
        "r",
        encoding="utf-8"
    ) as file:
        saved_data = json.load(file)

    assert len(saved_data["data"]) == 1

    assert (
        saved_data["data"][0]["id"]
        == "alert-test-1"
    )


def test_collect_alerts_handles_api_failure(
        monkeypatch,
        caplog
):

    def fake_failed_get(
            url,
            params,
            headers,
            timeout
    ):
        raise alerts.requests.RequestException(
            "Test alert API failure"
        )

    monkeypatch.setattr(
        alerts.requests,
        "get",
        fake_failed_get
    )

    result = alerts.collect_alerts()

    assert result is None

    assert (
        "Alert API request failed"
        in caplog.text
    )