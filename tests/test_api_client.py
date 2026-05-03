import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from unittest.mock import patch, MagicMock
from api_client import ApiClient

def test_build_url_contains_required_params():
    client = ApiClient(app_key=12345, app_secret="secret", base_url="https://open.goofish.pro")
    url = client._build_url("/api/open/test", '{"x":1}', timestamp=1700000000)
    assert "appid=12345" in url
    assert "timestamp=1700000000" in url
    assert "sign=" in url

def test_post_returns_data_on_success():
    client = ApiClient(app_key=12345, app_secret="secret", base_url="https://open.goofish.pro")
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"code": 0, "msg": "OK", "data": {"product_id": 999}}
    mock_resp.raise_for_status = MagicMock()
    with patch("api_client.requests.post", return_value=mock_resp) as mock_post:
        result = client.post("/api/open/test", {"x": 1})
    assert result == {"product_id": 999}

def test_post_raises_on_api_error():
    client = ApiClient(app_key=12345, app_secret="secret", base_url="https://open.goofish.pro")
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"code": 100004, "msg": "param error", "data": None}
    mock_resp.raise_for_status = MagicMock()
    with patch("api_client.requests.post", return_value=mock_resp):
        try:
            client.post("/api/open/test", {"x": 1})
            assert False, "should have raised"
        except Exception as e:
            assert "100004" in str(e)
