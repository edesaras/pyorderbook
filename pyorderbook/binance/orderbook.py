import asyncio
import aiohttp
import websockets
import json
from sortedcontainers import SortedDict


class BinanceOrderBook:
    def __init__(self, symbol: str, depth_limit: int = 1000):
        self.symbol = symbol.strip().upper()  # Ensure uppercase and no extra spaces
        self.depth_limit = depth_limit
        self.bids = SortedDict(lambda x: -x)
        self.asks = SortedDict()
        self.last_update_id = None
        self.listeners = []  # List of callbacks

    def add_listener(self, callback):
        """
        Add a callback to be notified of updates.
        """
        self.listeners.append(callback)

    async def fetch_snapshot(self):
        """
        Fetch the initial order book snapshot from Binance REST API.
        """
        url = f"https://api.binance.com/api/v3/depth?symbol={self.symbol}&limit={self.depth_limit}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    self._apply_snapshot(data)
                else:
                    raise Exception(f"Failed to fetch snapshot: {response.status}, {await response.text()}")

    def _apply_snapshot(self, snapshot: dict):
        """
        Apply the initial snapshot to the order book.
        """
        self.bids.clear()
        self.asks.clear()
        for price, quantity in snapshot["bids"]:
            self.bids[float(price)] = float(quantity)
        for price, quantity in snapshot["asks"]:
            self.asks[float(price)] = float(quantity)
        self.last_update_id = snapshot["lastUpdateId"]

    async def listen_for_updates(self):
        """
        Listen to Binance WebSocket for real-time updates.
        """
        url = f"wss://stream.binance.com:9443/ws/{self.symbol.lower()}@depth@100ms"
        async with websockets.connect(url) as websocket:
            while True:
                try:
                    message = await websocket.recv()
                    updates = json.loads(message)
                    self._process_update(updates)
                except Exception as e:
                    print(f"WebSocket error: {e}")


    def _process_update(self, updates: dict):
        """
        Process incremental updates and notify listeners.
        """
        # print(f"Processing update: U={updates['U']}, u={updates['u']}, last_update_id={self.last_update_id}")

        # Check for gaps
        if updates["U"] > self.last_update_id + 1:
            # print("Gap detected. Re-syncing.")
            asyncio.create_task(self.fetch_snapshot())
            return

        if updates["u"] <= self.last_update_id:
            # print("Outdated update. Ignored.")
            return

        # Apply updates
        for price, quantity in updates["b"]:
            price = float(price)
            quantity = float(quantity)
            if quantity == 0:
                self.bids.pop(price, None)
            else:
                self.bids[price] = quantity

        for price, quantity in updates["a"]:
            price = float(price)
            quantity = float(quantity)
            if quantity == 0:
                self.asks.pop(price, None)
            else:
                self.asks[price] = quantity

        self.last_update_id = updates["u"]

        # Validate spread
        best_bid, best_ask = self.get_top_of_book()
        if best_bid and best_ask and best_bid[0] >= best_ask[0]:
            # print(f"Negative spread detected: {best_bid}, {best_ask}. Re-syncing.")
            asyncio.create_task(self.fetch_snapshot())

        # Notify listeners
        for callback in self.listeners:
            callback(self)

    def get_top_of_book(self):
        """
        Get the best bid and ask prices.
        """
        best_bid = self.bids.peekitem(0) if self.bids else None
        best_ask = self.asks.peekitem(0) if self.asks else None
        return best_bid, best_ask

    def get_spread(self):
        """
        Calculate the bid-ask spread.
        """
        best_bid, best_ask = self.get_top_of_book()
        if best_bid and best_ask:
            return best_ask[0] - best_bid[0]
        return None

    async def start(self):
        """
        Start the order book: fetch snapshot and listen for updates.
        """
        await self.fetch_snapshot()
        # print(len(self.bids), len(self.asks)) # debug call
        await self.listen_for_updates()
