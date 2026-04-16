from fastapi import FastAPI, HTTPException
import uvicorn
from data_fetcher import fetch_all_data

app = FastAPI(title="Equity Research API")

@app.get("/stock")
def get_stock_data(ticker: str):
    """
    ChatGPT natively requests this URL (e.g. /stock?ticker=IGL.NS).
    It will return the massive block of scraped Yahoo/News context.
    """
    try:
        # Re-using the exact scraping logic we built today!
        data_context = fetch_all_data(ticker)
        return {"ticker": ticker, "context": data_context}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
