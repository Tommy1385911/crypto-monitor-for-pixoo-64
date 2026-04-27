import requests
from pixoo import Pixoo
import time
import socket
import json
import urllib.request
from datetime import datetime
from char_fonts import CHAR_FONT_5x7, CHAR_FONT_3x5

# 定義幣種顯示位置的 Y 偏移
y_offsets = [23, 30, 37, 44, 51, 58]

# ==========================================
#        自動抓取 Pixoo IP (雲端 API)
# ==========================================

def auto_discover_pixoo():
    """
    透過 Divoom 雲端 API 自動搜尋區網內的 Pixoo 裝置。
    使用 urllib (內建)，不依賴 requests。
    找不到時退回手動輸入。
    """
    print("=" * 50)
    print("       Pixoo 裝置自動搜尋")
    print("=" * 50)

    retry_delay = 5  # 搜尋失敗後等幾秒重試

    while True:
        print("\n🔍 正在透過 Divoom 雲端 API 搜尋...")

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
                print(f"❌ 未找到裝置，{retry_delay} 秒後重試... (Ctrl+C 取消)")
                time.sleep(retry_delay)
                continue

            if len(devices) == 1:
                ip = devices[0]["ip"]
                print(f"✅ 找到裝置: {devices[0]['name']} @ {ip}")
                return ip

            # 多台裝置，讓使用者選擇
            print(f"\n找到 {len(devices)} 台裝置：")
            for idx, dev in enumerate(devices):
                print(f"  [{idx + 1}] {dev['name']} @ {dev['ip']}")

            while True:
                choice = input(f"請選擇裝置 (1-{len(devices)}): ").strip()
                if choice.isdigit() and 1 <= int(choice) <= len(devices):
                    selected = devices[int(choice) - 1]
                    print(f"✅ 已選擇: {selected['name']} @ {selected['ip']}")
                    return selected["ip"]
                print("無效選擇，請重試。")

        except KeyboardInterrupt:
            print("\n已取消搜尋。")
            raise SystemExit(0)
        except Exception as e:
            print(f"❌ 搜尋失敗: {e}")
            print(f"   {retry_delay} 秒後重試... (Ctrl+C 取消)")
            time.sleep(retry_delay)

# ==========================================
#        繪圖函式
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
#        邏輯函式
# ==========================================

def get_price_color(current_price, previous_close_price):
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
    """批量取得價格，一次 API 呼叫拿所有幣種"""
    prices = {}
    try:
        url = 'https://fapi.binance.com/fapi/v1/ticker/price'
        response = requests.get(url, timeout=5).json()
        # 建立查找表
        price_map = {item['symbol']: float(item['price']) for item in response}
        for symbol in symbols:
            key = f'{symbol}USDT'
            if key in price_map:
                prices[symbol] = round(price_map[key], 8)
            else:
                print(f"⚠️  找不到 {key} 的價格")
    except Exception as e:
        print(f"Error fetching prices: {e}")
    # 回傳已成功取得的部分（可能為空 dict，但不回傳 None）
    return prices

def get_previous_hour_close_prices(symbols):
    """逐一取得 K 線，單一幣種失敗不影響其他"""
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
                print(f"⚠️  {symbol} K線取得失敗: {e}")
    return close_prices

# ==========================================
#        主程式
# ==========================================

def main():
    # ===== 自動搜尋 Pixoo IP =====
    pixoo_ip = auto_discover_pixoo()

    print(f"\n正在連接 Pixoo @ {pixoo_ip}...")
    try:
        pix = Pixoo(pixoo_ip, 64, True)
    except Exception as e:
        print(f"無法連接 Pixoo (IP: {pixoo_ip}): {e}")
        return

    # 1. 初始背景
    pix.fill((0, 0, 0))

    # 2. 選幣
    selected_symbols = []
    print("請輸入想顯示的幣種（最多六種）：")
    while len(selected_symbols) < 6:
        symbol = input("幣種代碼 (Enter 使用預設): ").strip().upper()
        if symbol == "":
            if not selected_symbols:
                selected_symbols = ['BTC', 'ETH', 'SOL', 'BNB', 'DOGE', 'XRP']
            break
        if symbol not in selected_symbols:
            selected_symbols.append(symbol)
    print(f"已選擇：{selected_symbols}")

    # 3. 初始化數據緩存
    cached_prices = {s: 0.0 for s in selected_symbols}
    cached_prev_close = {s: 0.0 for s in selected_symbols}

    last_kline_update = 0
    KLINE_INTERVAL = 3600

    print("初始化數據中...")
    try:
        p = get_crypto_prices(selected_symbols)
        if p: cached_prices.update(p)
        k = get_previous_hour_close_prices(selected_symbols)
        if k:
            cached_prev_close.update(k)
            last_kline_update = time.time()
    except Exception as e:
        print(f"初始化數據部分失敗 (將在迴圈中重試): {e}")

    print("開始執行 (自動對齊 00, 10, 20 秒)...")

    # --- 主迴圈 ---
    while True:
        try:
            # --- A. 數據更新 ---
            new_prices = get_crypto_prices(selected_symbols)
            if new_prices: cached_prices.update(new_prices)

            if time.time() - last_kline_update > KLINE_INTERVAL:
                new_klines = get_previous_hour_close_prices(selected_symbols)
                if new_klines:
                    cached_prev_close.update(new_klines)
                    last_kline_update = time.time()

            # --- B. 繪圖 ---
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

            # --- C. 智慧對齊休眠 ---
            now = datetime.now()
            remainder = now.second % 10
            sleep_time = 10 - remainder - (now.microsecond / 1_000_000)
            if sleep_time < 0: sleep_time += 10
            time.sleep(sleep_time + 0.05)

        except KeyboardInterrupt:
            print("Program interrupted.")
            break
        except (ConnectionError, OSError, BrokenPipeError) as e:
            # Pixoo 斷線，嘗試重連
            print(f"⚠️  Pixoo 連線中斷: {e}")
            print("   5 秒後嘗試重連...")
            time.sleep(5)
            try:
                pix = Pixoo(pixoo_ip, 64, True)
                print("✅ 重連成功!")
            except Exception as re:
                print(f"❌ 重連失敗: {re}")
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(10)

if __name__ == "__main__":
    main()
