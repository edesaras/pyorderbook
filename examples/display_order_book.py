import asyncio
from rich.console import Console
from rich.table import Table
from pyorderbook.binance.orderbook import BinanceOrderBook


async def display_order_book(order_book):
    """
    Display the order book in real-time using rich tables.
    """
    console = Console()
    while True:
        # Clear the console
        console.clear()

        # Create a new table
        table = Table(title=f"Order Book: {order_book.symbol}")

        table.add_column("Type", style="bold cyan")
        table.add_column("Price", justify="right")
        table.add_column("Volume", justify="right")

        # Add top 5 bids
        for price, volume in list(order_book.bids.items())[:5]:
            table.add_row("Bid", f"{price:.2f}", f"{volume:.2f}")

        # Add top 5 asks
        for price, volume in list(order_book.asks.items())[:5]:
            table.add_row("Ask", f"{price:.2f}", f"{volume:.2f}")

        # Print the table
        console.print(table)

        # Update every 100ms
        await asyncio.sleep(0.1)


async def main():
    """
    Main script for real-time order book monitoring with rich.
    """
    symbol = "BTCUSDT"
    order_book = BinanceOrderBook(symbol=symbol)

    # Start the order book updates in the background
    asyncio.create_task(order_book.start())

    # Display the order book in real time
    await display_order_book(order_book)


if __name__ == "__main__":
    asyncio.run(main())
