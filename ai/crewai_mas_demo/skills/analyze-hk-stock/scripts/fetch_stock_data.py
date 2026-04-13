#!/usr/bin/env python3
# scripts/fetch_stock_data.py
import akshare as ak
import argparse
import json
import sys

def fetch_hk_stock_data(symbol):
    try:
        # 获取港股实时行情
        stock_info = ak.stock_hk_spot(symbol=symbol)
        if stock_info.empty:
            return {"error": "No data found for symbol"}

        data = stock_info.iloc[0].to_dict()
        return {
            "symbol": data.get('symbol'),
            "name": data.get('name'),
            "price": data.get('last_price'),
            "change": data.get('change_price'),
            "change_pct": data.get('change_rate'),
            "volume": data.get('volume'),
            "amount": data.get('amount'),
            "high": data.get('high_price'),
            "low": data.get('low_price'),
            "open": data.get('open_price'),
            "prev_close": data.get('pre_price')
        }
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch Hong Kong stock data")
    parser.add_argument('--symbol', type=str, required=True, help='HK stock symbol (e.g. 0700.HK)')
    args = parser.parse_args()

    result = fetch_hk_stock_data(args.symbol)
    print(json.dumps(result, ensure_ascii=False))
