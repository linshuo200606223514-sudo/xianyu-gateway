import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from sign import gen_sign

def test_sign_deterministic():
    body = '{"title":"test"}'
    timestamp = 1700000000
    app_key = 203413189371893
    app_secret = "o9wl81dncmvby3ijpq7eur456zhgtaxs"
    result = gen_sign(body, timestamp, app_key, app_secret)
    assert result == gen_sign(body, timestamp, app_key, app_secret)
    assert len(result) == 32

def test_sign_different_body():
    timestamp = 1700000000
    app_key = 203413189371893
    app_secret = "o9wl81dncmvby3ijpq7eur456zhgtaxs"
    s1 = gen_sign('{"a":1}', timestamp, app_key, app_secret)
    s2 = gen_sign('{"a":2}', timestamp, app_key, app_secret)
    assert s1 != s2
