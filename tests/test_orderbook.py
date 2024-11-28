import pytest
from pyorderbook.binance.orderbook import BinanceOrderBook

@pytest.fixture
def mock_snapshot():
    return {
        "lastUpdateId": 1000,
        "bids": [["100.0", "5.0"], ["99.0", "3.0"]],
        "asks": [["101.0", "2.0"], ["102.0", "4.0"]],
    }

def test_apply_snapshot(mock_snapshot):
    ob = BinanceOrderBook(symbol="BTCUSDT")
    ob._apply_snapshot(mock_snapshot)
    assert ob.last_update_id == 1000
    assert ob.bids[100.0] == 5.0
    assert ob.asks[101.0] == 2.0

def test_get_top_of_book(mock_snapshot):
    ob = BinanceOrderBook(symbol="BTCUSDT")
    ob._apply_snapshot(mock_snapshot)
    best_bid, best_ask = ob.get_top_of_book()
    assert best_bid == (100.0, 5.0)
    assert best_ask == (101.0, 2.0)

def test_get_spread(mock_snapshot):
    ob = BinanceOrderBook(symbol="BTCUSDT")
    ob._apply_snapshot(mock_snapshot)
    spread = ob.get_spread()
    assert spread == 1.0
