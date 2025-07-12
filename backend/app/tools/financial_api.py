import os
from alpha_vantage.fundamentaldata import FundamentalData
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")

class FinancialAPIError(Exception):
    pass

def get_financial_data(company_symbol: str) -> dict:
    """
    Fetches key financial metrics for a given company symbol using Alpha Vantage.
    Returns:
        dict: filtered financial data or {"error": str}
    """
    if not API_KEY:
        return {"error": "Alpha Vantage API key not found."}

    try:
        fd = FundamentalData(key=API_KEY, output_format='json')
        data, _ = fd.get_company_overview(symbol=company_symbol)
        if not data:
            return {"error": f"No data found for symbol {company_symbol}"}
        filtered_data = {
            "Symbol": data.get("Symbol"),
            "AssetType": data.get("AssetType"),
            "Name": data.get("Name"),
            "Description": data.get("Description"),
            "MarketCapitalization": data.get("MarketCapitalization"),
            "EBITDA": data.get("EBITDA"),
            "PERatio": data.get("PERatio"),
            "BookValue": data.get("BookValue"),
            "DividendPerShare": data.get("DividendPerShare"),
            "RevenuePerShareTTM": data.get("RevenuePerShareTTM"),
            "ProfitMargin": data.get("ProfitMargin"),
            "52WeekHigh": data.get("52WeekHigh"),
            "52WeekLow": data.get("52WeekLow"),
        }
        return filtered_data
    except Exception as e:
        return {"error": f"FinancialAPIError: {e}"}
