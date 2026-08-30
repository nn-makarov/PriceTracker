from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import os
import logging

from app import models, schemas, crud
from app.database import engine, get_db
from app.yamarket_parser import parse_yamarket

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("pricetracker")

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="PriceTracker API", version="2.0")

app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.get("/api/search")
async def search_products(query: str = ""):
    """Поиск товара по URL Яндекс.Маркет."""
    query = query.strip()

    if "market.yandex.ru" not in query:
        return {"results": [], "message": "Введите URL Яндекс.Маркет для поиска товара"}

    result = await parse_yamarket(query)
    if result.get("success"):
        return {
            "results": [{
                "product_id": result["product_id"],
                "title": result["title"],
                "price": result["price"],
                "url": result["url"],
                "source": result["source"],
            }]
        }
    return {"results": [], "error": result.get("error", "Ошибка парсинга")}


@app.post("/api/track")
def track_product(product_data: schemas.ProductCreate, db: Session = Depends(get_db)):
    """Добавить товар в отслеживание."""
    try:
        product = crud.create_product(db, product_data)
        logger.info(f"Товар добавлен: ID {product.id}")
        return product
    except Exception:
        # Наружу не отдаём подробности ошибки, только в лог.
        logger.exception("Не удалось добавить товар")
        raise HTTPException(status_code=500, detail="Не удалось добавить товар")


@app.get("/api/tracked-products")
def get_tracked_products(db: Session = Depends(get_db)):
    """Список отслеживаемых товаров."""
    return crud.get_products(db)


@app.delete("/api/products/{product_id}", status_code=204)
def delete_product(product_id: int, db: Session = Depends(get_db)):
    """Удалить товар вместе с историей цен."""
    if not crud.delete_product(db, product_id):
        raise HTTPException(status_code=404, detail="Товар не найден")
    logger.info(f"Товар удалён: ID {product_id}")


@app.get("/api/stats/{product_id}")
def get_product_stats(product_id: int, db: Session = Depends(get_db)):
    """История и статистика цены по товару."""
    product = crud.get_product(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден")

    history = crud.get_price_history(db, product_id)
    return {
        "product": product,
        "price_history": history,
        "stats": {
            "current_price": product.current_price,
            "total_records": len(history),
            "price_change": history[-1].price - history[0].price if len(history) > 1 else 0,
        },
    }


@app.get("/")
async def serve_frontend():
    return FileResponse("app/static/index.html")


@app.get("/{path:path}")
async def serve_static(path: str):
    # Несуществующие API-пути должны отдавать 404, а не главную страницу.
    if path.startswith("api/"):
        raise HTTPException(status_code=404, detail="Not found")
    static_path = f"app/static/{path}"
    if os.path.exists(static_path) and os.path.isfile(static_path):
        return FileResponse(static_path)
    return FileResponse("app/static/index.html")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
