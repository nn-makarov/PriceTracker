from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List
from app import models, schemas, crud
from app.database import engine, get_db
from app.yamarket_parser import parse_yamarket
from sqlalchemy import text 
import os
import logging

load_dotenv()


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("pricetracker")


models.Base.metadata.create_all(bind=engine)


app = FastAPI(title="PriceTracker API", version="1.0")


app.mount("/static", StaticFiles(directory="app/static"), name="static")



@app.get("/api/parse/yamarket")
async def parse_ym_product(url: str):
    """
    Парсинг Яндекс.Маркет по URL
    """
    return await parse_yamarket(url)

@app.get("/api/search")
async def search_products(query: str = ""):
    """
    Поиск товаров: принимает запрос или URL Яндекс.Маркет
    """
    query = query.strip()
    
    
    if "market.yandex.ru" in query:
        result = await parse_yamarket(query)
        
        if result.get('success'):
            return {
                "results": [{
                    "product_id": result['product_id'],
                    "title": result['title'],
                    "price": result['price'],
                    "url": result['url'],
                    "source": result['source']
                }]
            }
        else:
            return {
                "results": [],
                "error": result.get('error', 'Ошибка парсинга')
            }
    else:
        return {
            "results": [],
            "message": "Введите URL Яндекс.Маркет для поиска товара"
        }
    

@app.post("/api/track")
def track_product(product_data: schemas.ProductCreate, db: Session = Depends(get_db)):
    """Добавление товара для отслеживания"""
    try:
        product = crud.create_product(db, product_data)
        logger.info(f"✅ Product tracked: ID {product.id}")
        return product
    except Exception as e:
        logger.error(f"❌ Track failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to track product: {str(e)}")

@app.get("/api/stats/{product_id}")
def get_product_stats(product_id: int, db: Session = Depends(get_db)):
    """Статистика по цене товара"""
    logger.info(f"📊 Get stats for product: {product_id}")

    product = crud.get_product(db, product_id)
    if not product:
        logger.warning(f"Product not found: {product_id}")
        raise HTTPException(status_code=404, detail="Product not found")
    
    history = crud.get_price_history(db, product_id)
    logger.info(f"✅ Stats retrieved: {len(history)} price records")
    
    return {
        "product": product,
        "price_history": history,
        "stats": {
            "current_price": product.current_price,
            "total_records": len(history),
            "price_change": history[-1].price - history[0].price if len(history) > 1 else 0
        }
    }

@app.get("/api/test-db")
def test_db(db: Session = Depends(get_db)):
    """Тестовый endpoint для проверки БД"""
    try:
        db.execute(text("SELECT 1"))
        return {"status": "Database connected successfully"}
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/tracked-products")
def get_tracked_products(db: Session = Depends(get_db)):
    """Получить все отслеживаемые товары"""
    return crud.get_products(db)

@app.get("/")
async def serve_frontend():
    return FileResponse("app/static/index.html")

@app.get("/{path:path}")
async def serve_static(path: str):
    static_path = f"app/static/{path}"
    if os.path.exists(static_path):
        return FileResponse(static_path)
    return FileResponse("app/static/index.html")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)