import warnings
warnings.filterwarnings("ignore", category=RuntimeWarning)

import yfinance as yf
import requests
from bs4 import BeautifulSoup
try:
    from ddgs import DDGS
except ImportError:
    from duckduckgo_search import DDGS
import pandas as pd

def fetch_financial_data(ticker_symbol: str) -> dict:
    """Fetches comprehensive specific fundamental and market data using yfinance."""
    stock = yf.Ticker(ticker_symbol)
    
    # Get basic info
    info = stock.info
    
    # Get financials (Income Statement)
    try:
        financials = stock.financials.fillna(0)
    except:
        financials = pd.DataFrame()
        
    # Get balance sheet
    try:
        balance_sheet = stock.balance_sheet.fillna(0)
    except:
        balance_sheet = pd.DataFrame()
        
    # Get cashflow
    try:
        cashflow = stock.cashflow.fillna(0)
    except:
        cashflow = pd.DataFrame()
        
    data = {
        "Company Name": info.get("longName", ticker_symbol),
        "Sector": info.get("sector", "N/A"),
        "Industry": info.get("industry", "N/A"),
        "Market Cap": info.get("marketCap", "N/A"),
        "Current Price": info.get("currentPrice", "N/A"),
        "52 Week High": info.get("fiftyTwoWeekHigh", "N/A"),
        "52 Week Low": info.get("fiftyTwoWeekLow", "N/A"),
        "Trailing P/E": info.get("trailingPE", "N/A"),
        "Forward P/E": info.get("forwardPE", "N/A"),
        "Price to Book": info.get("priceToBook", "N/A"),
        "Return on Equity (ROE)": info.get("returnOnEquity", "N/A"),
        "Debt to Equity": info.get("debtToEquity", "N/A"),
        "Total Debt": info.get("totalDebt", "N/A"),
        "Total Cash": info.get("totalCash", "N/A"),
        "Free Cashflow": info.get("freeCashflow", "N/A"),
        "Operating Margins": info.get("operatingMargins", "N/A"),
        "EBITDA Margins": info.get("ebitdaMargins", "N/A"),
        "Profit Margins": info.get("profitMargins", "N/A"),
        "Revenue Growth": info.get("revenueGrowth", "N/A"),
        "Earnings Growth": info.get("earningsGrowth", "N/A"),
        "Dividend Yield": info.get("dividendYield", "N/A"),
        "Beta": info.get("beta", "N/A"),
        "Business Summary": info.get("longBusinessSummary", "N/A"),
        "Recent Financials (Income Statement)": financials.head(10).to_string() if not financials.empty else "N/A",
        "Recent Balance Sheet": balance_sheet.head(10).to_string() if not balance_sheet.empty else "N/A",
        "Recent Cash Flow": cashflow.head(10).to_string() if not cashflow.empty else "N/A",
    }
    
    return data

def fetch_screener_data(ticker_symbol: str) -> str:
    """Scrapes historical 10-year fundamentals from Screener.in"""
    clean_ticker = ticker_symbol.replace('.NS', '').replace('.BO', '')
    url = f"https://www.screener.in/company/{clean_ticker}/consolidated/"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            # Fallback to standalone if consolidated doesn't exist
            url_standalone = f"https://www.screener.in/company/{clean_ticker}/"
            response = requests.get(url_standalone, headers=headers, timeout=10)
            if response.status_code != 200:
                return "Screener data not found for this ticker."
                
        soup = BeautifulSoup(response.text, 'html.parser')
        
        screener_text = "=== SCREENER.IN 10-YEAR FUNDAMENTALS ===\n"
        sections = soup.find_all('section', id=['profit-loss', 'balance-sheet', 'cash-flow', 'ratios'])
        
        for sec in sections:
            header = sec.find('h2')
            if header:
                screener_text += f"\n--- {header.text.strip()} ---\n"
            
            table = sec.find('table')
            if table:
                rows = table.find_all('tr')
                for row in rows:
                    cols = row.find_all(['th', 'td'])
                    row_text = " | ".join([c.text.strip().replace('\n', ' ') for c in cols])
                    screener_text += row_text + "\n"
                    
        return screener_text
    except Exception as e:
        return f"Error fetching Screener data: {e}"

def fetch_nse_announcements(ticker_symbol: str) -> str:
    """Scrapes recent corporate announcements from NSE India."""
    clean_ticker = ticker_symbol.replace('.NS', '').replace('.BO', '')
    url = f"https://www.nseindia.com/api/corporate-announcements?index=equities&symbol={clean_ticker}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": f"https://www.nseindia.com/get-quotes/equity?symbol={clean_ticker}"
    }
    
    try:
        # NSE requires a session cookie first
        session = requests.Session()
        session.get("https://www.nseindia.com", headers=headers, timeout=5)
        
        response = session.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            announcements = data[:5] # top 5 recent filings
            result = "=== LATEST NSE CORPORATE ANNOUNCEMENTS ===\n"
            for item in announcements:
                desc = item.get('desc', item.get('subject', ''))
                date = item.get('an_dt', '')
                result += f"- [{date}] {desc}\n"
            return result
        return "NSE announcements not directly accessible right now."
    except Exception:
        return "Error querying NSE India API."

def fetch_latest_news(ticker_symbol: str, company_name: str) -> str:
    """Uses DuckDuckGo to search for recent news articles."""
    try:
        results = DDGS().text(f"{company_name} {ticker_symbol} investor news earnings", max_results=10)
        news_text = ""
        for r in results:
            news_text += f"- Title: {r.get('title')}\n  Body: {r.get('body')}\n\n"
        return news_text
    except Exception as e:
        return f"Could not fetch news: {e}"

def fetch_all_data(ticker_symbol: str) -> str:
    """Aggregates yFinance data and news into a readable text chunk for the LLM."""
    # Automatically append .NS for Indian stocks if no exchange suffix is provided
    if "." not in ticker_symbol:
        ticker_symbol = ticker_symbol.upper() + ".NS"
        
    financials = fetch_financial_data(ticker_symbol)
    company_name = financials.get("Company Name", ticker_symbol)
    
    news = fetch_latest_news(ticker_symbol, company_name)
    
    # Combine into a massive context string
    context = "=== FUNDAMENTAL AND MARKET DATA ===\n"
    for k, v in financials.items():
        if k not in ["Recent Financials (Income Statement)", "Recent Balance Sheet", "Recent Cash Flow"]:
            context += f"{k}: {v}\n"
    
    context += "\n=== FINANCIAL STATEMENTS ===\n"
    context += f"Income Statement Snapshot:\n{financials.get('Recent Financials (Income Statement)')}\n\n"
    context += f"Balance Sheet Snapshot:\n{financials.get('Recent Balance Sheet')}\n\n"
    context += f"Cash Flow Snapshot:\n{financials.get('Recent Cash Flow')}\n\n"
    
    screener_data = fetch_screener_data(ticker_symbol)
    context += "\n" + screener_data + "\n\n"
    
    nse_data = fetch_nse_announcements(ticker_symbol)
    context += nse_data + "\n\n"

    context += "=== LATEST NEWS & DEVELOPMENTS ===\n"
    context += news
    
    return context
