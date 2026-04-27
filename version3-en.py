import requests
from pixoo import Pixoo
import time
import socket
import json
import urllib.request
from datetime import datetime
from char_fonts import CHAR_FONT_5x7, CHAR_FONT_3x5

# Y-offset positions for each coin row on the 64x64 display
y_offsets = [23, 30, 37, 44, 51, 58]

# ==========================================
#        Auto-discover Pixoo IP (Cloud API)
# ==========================================

def auto_discover_pixoo():
    """
    Auto-discover Pixoo devices on the local network via Divoom Cloud API.
    Uses urllib (built-in), no dependency on requests.
    Retries indefinitely until a device is found.
    """
    print("=" * 50)
    print("       Pixoo Device Auto-Discovery")
    print("=" * 50)

    retry_delay = 5  # seconds between retries

    while True:
        print("\n🔍 Searching via Divoom Cloud API...")

        try:
            url = "https://app.divoom-gz.com/Device/ReturnSameLANDevice"
            req = urllib.request.Request(url, data=b"", method="POST")
            req.add_header("Content-Type", "application/json")

            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            devices = []
            if data.get("ReturnCode") == 0 and data.get("DeviceList"):
                for dev in data["DeviceList"]:
                    ip = dev.get("DevicePrivateIP", "")
                    name = dev.get("DeviceName", "Unknown")
                    if ip:
                        devices.append({"ip": ip, "name": name})

            if not devices:
                print(f"❌ No device found. Retrying in {retry_delay}s... (Ctrl+C to cancel)")
                time.sleep(retry_delay)
                continue

            if len(devices) == 1:
                ip = devices[0]["ip"]
                print(f"✅ Found device: {devices[0]['name']} @ {ip}")
                return ip

            # Multiple devices found, let user choose
            print(f"\nFound {len(devices)} devices:")
            for idx, dev in enumerate(devices):
                print(f"  [{idx + 1}] {dev['name']} @ {dev['ip']}")

            while True:
                choice = input(f"Select device (1-{len(devices)}): ").strip()
                if choice.isdigit() and 1 <= int(choice) <= len(devices):
                    selected = devices[int(choice) - 1]
                    print(f"✅ Selected: {selected['name']} @ {selected['ip']}")
                    return selected["ip"]
                print("Invalid choice, please try again.")

        except KeyboardInterrupt:
            print("\nSearch cancelled.")
            raise SystemExit(0)
        except Exception as e:
            print(f"❌ Search failed: {e}")
            print(f"   Retrying in {retry_delay}s... (Ctrl+C to cancel)")
            time.sleep(retry_delay)

# ==========================================
#        Drawing Functions
# ==========================================

def draw_pixel(pix, x, y, color=(255, 255, 255)):
    if 0 <= x < 64 and 0 <= y < 64:
        pix.draw_pixel((x, y), color)

def draw_char_5x7(pix, char, start_x, start_y, color=(255, 255, 255)):
    if char not in CHAR_FONT_5x7:
        return
    char_data = CHAR_FONT_5x7[char]
    for y, row in enumerate(char_data):
        for x, pixel in enumerate(row):
            if pixel == 1:
                draw_pixel(pix, start_x + x, start_y + y, color)

def draw_text_5x7(pix, text, start_x, start_y, color=(255, 255, 255), spacing=1):
    x_offset = 0
    for char in text:
        draw_char_5x7(pix, char, start_x + x_offset, start_y, color)
        x_offset += len(CHAR_FONT_5x7["0"][0]) + spacing

def draw_char_3x5(pix, char, start_x, start_y, color=(255, 255, 255)):
    if char not in CHAR_FONT_3x5:
        return
    char_data = CHAR_FONT_3x5[char]
    for y, row in enumerate(char_data):
        for x, pixel in enumerate(row):
            if pixel == 1:
                draw_pixel(pix, start_x + x, start_y + y, color)

def draw_text_3x5(pix, text, start_x, start_y, color=(255, 255, 255), spacing=1):
    x_offset = 0
    for char in text:
        draw_char_3x5(pix, char, start_x + x_offset, start_y, color)
        x_offset += len(CHAR_FONT_3x5["A"][0]) + spacing

def draw_vertical_line(pix, start_x, start_y, length, color=(0, 255, 0)):
    for y in range(start_y, start_y + length):
        draw_pixel(pix, start_x, y, color)

def draw_horizontal_line(pix, start_y, color=(0, 255, 0)):
    for x in range(64):
        draw_pixel(pix, x, start_y, color)

def draw_triangle(pix, start_x, start_y, inverted=False, color=(255, 0, 0)):
    triangle = [
        [0, 0, 0, 1, 0, 0, 0],
        [0, 0, 1, 1, 1, 0, 0],
        [0, 1, 1, 1, 1, 1, 0],
        [1, 1, 1, 1, 1, 1, 1],
    ]
    if inverted:
        triangle = triangle[::-1]
    for y, row in enumerate(triangle):
        for x, pixel in enumerate(row):
            if pixel == 1:
                draw_pixel(pix, start_x + x, start_y + y, color)

def draw_rectangle(pix, start_x, start_y, end_x, end_y, color):
    for y in range(start_y, end_y + 1):
        for x in range(start_x, end_x + 1):
            draw_pixel(pix, x, y, color)

# ==========================================
#        Logic Functions
# ==========================================

def get_price_color(current_price, previous_close_price):
    """Red = up, Green = down, White = unchanged"""
    if previous_close_price == 0:
        return (255, 255, 255)
    change = (current_price - previous_close_price) / previous_close_price * 100
    if change > 0:
        return (255, 0, 0)
    elif change < 0:
        return (0, 255, 0)
    else:
        return (255, 255, 255)

def get_current_time_and_date():
    now = datetime.now()
    current_date = now.strftime("%b-%d").upper()
    current_time = now.strftime("%H:%M:%S")
    current_weekday = now.strftime("%a").upper()
    return current_date, current_time, current_weekday

def format_price_to_8_chars(price):
    """Format price to fit exactly 8 characters on the display"""
    price_str = f"{price:.8f}"
    if len(price_str) > 8:
        int_part = str(int(price))
        decimals_allowed = 8 - len(int_part) - 1
        if decimals_allowed > 0:
            price_str = f"{price:.{decimals_allowed}f}"
        else:
            price_str = int_part[:8]
    elif len(price_str) < 8:
        price_str = price_str.ljust(8, '0')
    return price_str

def get_crypto_prices(symbols):
    """Fetch all prices in a single API call (batch query)"""
    prices = {}
    try:
        url = 'https://fapi.binance.com/fapi/v1/ticker/price'
        response = requests.get(url, timeout=5).json()
        # Build lookup table
        price_map = {item['symbol']: float(item['price']) for item in response}
        for symbol in symbols:
            key = f'{symbol}USDT'
            if key in price_map:
                prices[symbol] = round(price_map[key], 8)
            else:
                print(f"⚠️  Price not found for {key}")
    except Exception as e:
        print(f"Error fetching prices: {e}")
    # Return whatever was successfully fetched (may be empty dict, never None)
    return prices

def get_previous_hour_close_prices(symbols):
    """Fetch K-line data per symbol; one failure won't affect the others"""
    close_prices = {}
    end_time = int(time.time() * 1000)
    start_time = end_time - 7200 * 1000
    with requests.Session() as session:
        for symbol in symbols:
            try:
                url = f'https://fapi.binance.com/fapi/v1/klines'
                params = {
                    'symbol': f'{symbol}USDT', 'interval': '1h', 'limit': 3,
                    'startTime': start_time, 'endTime': end_time
                }
                response = session.get(url, params=params, timeout=5).json()
                if len(response) > 1:
                    close_prices[symbol] = float(response[-2][4])
                else:
                    close_prices[symbol] = 0
            except Exception as e:
                print(f"⚠️  Failed to fetch K-line for {symbol}: {e}")
    return close_prices

# ==========================================
#        Main Program
# ==========================================

def main():
    # ===== Auto-discover Pixoo IP =====
    pixoo_ip = auto_discover_pixoo()

    print(f"\nConnecting to Pixoo @ {pixoo_ip}...")
    try:
        pix = Pixoo(pixoo_ip, 64, True)
    except Exception as e:
        print(f"Failed to connect to Pixoo (IP: {pixoo_ip}): {e}")
        return

    # 1. Clear display
    pix.fill((0, 0, 0))

    # 2. Select coins
    selected_symbols = []
    print("Enter coin symbols to display (up to 6):")
    while len(selected_symbols) < 6:
        symbol = input("Symbol (Enter for defaults): ").strip().upper()
        if symbol == "":
            if not selected_symbols:
                selected_symbols = ['BTC', 'ETH', 'SOL', 'BNB', 'DOGE', 'XRP']
            break
        if symbol not in selected_symbols:
            selected_symbols.append(symbol)
    print(f"Selected: {selected_symbols}")

    # 3. Initialize data cache
    cached_prices = {s: 0.0 for s in selected_symbols}
    cached_prev_close = {s: 0.0 for s in selected_symbols}

    last_kline_update = 0
    KLINE_INTERVAL = 3600  # Refresh K-line data every hour

    print("Initializing data...")
    try:
        p = get_crypto_prices(selected_symbols)
        if p: cached_prices.update(p)
        k = get_previous_hour_close_prices(selected_symbols)
        if k:
            cached_prev_close.update(k)
            last_kline_update = time.time()
    except Exception as e:
        print(f"Partial init failure (will retry in loop): {e}")

    print("Running (auto-aligned to 00, 10, 20s intervals)...")

    # --- Main loop ---
    while True:
        try:
            # --- A. Data update ---
            new_prices = get_crypto_prices(selected_symbols)
            if new_prices: cached_prices.update(new_prices)

            if time.time() - last_kline_update > KLINE_INTERVAL:
                new_klines = get_previous_hour_close_prices(selected_symbols)
                if new_klines:
                    cached_prev_close.update(new_klines)
                    last_kline_update = time.time()

            # --- B. Draw ---
            pix.fill((0, 0, 0))

            current_date, current_time, current_weekday = get_current_time_and_date()
            draw_text_3x5(pix, current_date, start_x=1, start_y=2, color=(255, 255, 255), spacing=1)
            draw_text_3x5(pix, current_weekday, start_x=49, start_y=2, color=(255, 255, 255), spacing=1)
            draw_text_5x7(pix, current_time, start_x=1, start_y=10, color=(255, 255, 255), spacing=1)

            for i, symbol in enumerate(selected_symbols):
                if i >= len(y_offsets): break

                price = cached_prices.get(symbol, 0.0)
                prev_close = cached_prev_close.get(symbol, 0.0)
                color = get_price_color(price, prev_close)

                display_symbol = symbol[:4]
                draw_text_3x5(pix, display_symbol, start_x=1, start_y=y_offsets[i], color=(255, 255, 255), spacing=1)

                formatted_price = format_price_to_8_chars(price)
                draw_text_3x5(pix, formatted_price, start_x=31, start_y=y_offsets[i], color=color, spacing=1)

                change = 0
                if prev_close > 0:
                    change = (price - prev_close) / prev_close * 100

                if change > 0:
                    draw_triangle(pix, start_x=21, start_y=y_offsets[i], inverted=False, color=(255, 0, 0))
                elif change < 0:
                    draw_triangle(pix, start_x=21, start_y=y_offsets[i], inverted=True, color=(0, 255, 0))

            pix.push()

            # --- C. Smart sleep alignment ---
            now = datetime.now()
            remainder = now.second % 10
            sleep_time = 10 - remainder - (now.microsecond / 1_000_000)
            if sleep_time < 0: sleep_time += 10
            time.sleep(sleep_time + 0.05)

        except KeyboardInterrupt:
            print("Program interrupted.")
            break
        except (ConnectionError, OSError, BrokenPipeError) as e:
            # Pixoo disconnected, attempt reconnection
            print(f"⚠️  Pixoo connection lost: {e}")
            print("   Reconnecting in 5s...")
            time.sleep(5)
            try:
                pix = Pixoo(pixoo_ip, 64, True)
                print("✅ Reconnected!")
            except Exception as re:
                print(f"❌ Reconnection failed: {re}")
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(10)

if __name__ == "__main__":
    main()
