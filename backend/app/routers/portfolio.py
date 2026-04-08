from fastapi import APIRouter, Header
from sqlalchemy import text
from ..database import SessionLocal
import yfinance as yf
from typing import Optional

router = APIRouter()

def parse_user_id(x_user_id: Optional[str]) -> Optional[int]:
    try:
        return int(x_user_id) if x_user_id else None
    except (ValueError, TypeError):
        return None


@router.post("/portfolio/add")
def add_stock(
    symbol:    str,
    quantity:  int,
    avg_price: float,
    x_user_id: Optional[str] = Header(None)  
):
    uid = parse_user_id(x_user_id)
    if not uid:
        return {"error": "Not logged in"}

    db = SessionLocal()
    try:
        db.execute(
            text("""
                INSERT INTO portfolio (symbol, quantity, avg_price, user_id)
                VALUES (:symbol, :quantity, :avg_price, :user_id)
            """),
            {"symbol": symbol.upper(), "quantity": quantity, "avg_price": avg_price, "user_id": uid}
        )
        db.commit()
    finally:
        db.close()
    return {"message": "Stock added successfully"}


@router.get("/portfolio")
def get_portfolio(x_user_id: Optional[str] = Header(None)):  
    uid = parse_user_id(x_user_id)
    if not uid:
        return []  

    db = SessionLocal()
    try:
        rows = db.execute(
            text("SELECT id, symbol, quantity, avg_price FROM portfolio WHERE user_id = :uid"),
            {"uid": uid}
        ).fetchall()
    finally:
        db.close()

    portfolio_data = []
    for row in rows:
        try:
            stock = yf.Ticker(row.symbol)
            hist  = stock.history(period="1d")
            current_price = float(hist["Close"].iloc[-1]) if not hist.empty else row.avg_price
        except Exception:
            current_price = row.avg_price

        pnl = (current_price - row.avg_price) * row.quantity
        portfolio_data.append({
            "id":            row.id,
            "symbol":        row.symbol,
            "quantity":      row.quantity,
            "avg_price":     row.avg_price,
            "current_price": round(current_price, 2),
            "pnl":           round(pnl, 2)
        })

    return portfolio_data


@router.delete("/portfolio/delete/{stock_id}")
def delete_stock(stock_id: int, x_user_id: Optional[str] = Header(None)):  
    uid = parse_user_id(x_user_id)
    if not uid:
        return {"error": "Not logged in"}

    db = SessionLocal()
    try:
        db.execute(
            text("DELETE FROM portfolio WHERE id = :id AND user_id = :uid"),
            {"id": stock_id, "uid": uid}
        )
        db.commit()
    finally:
        db.close()
    return {"message": "Stock deleted"}