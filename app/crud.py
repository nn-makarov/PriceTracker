from sqlalchemy.orm import Session
from .models import Product, PriceHistory
from . import schemas

def get_product(db: Session, product_id: int):
    return db.query(Product).filter(Product.id == product_id).first()

def get_products(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Product).offset(skip).limit(limit).all()

def get_product_by_url(db: Session, url: str):
    return db.query(Product).filter(Product.url == url).first()

def create_product(db: Session, product: schemas.ProductCreate):

    if db_product := get_product_by_url(db, product.url):
        return db_product
    
    db_product = Product(
        title=product.title,
        url=product.url,
        current_price=product.current_price
    )
    db.add(db_product)
    db.flush()  
    
    
    db.add(PriceHistory(
        product_id=db_product.id,
        price=product.current_price
    ))
    
    db.commit()  
    db.refresh(db_product)
    return db_product

def get_price_history(db: Session, product_id: int, limit: int = 30):
    return db.query(PriceHistory).filter(
        PriceHistory.product_id == product_id
    ).order_by(PriceHistory.created_at.desc()).limit(limit).all()


def delete_product(db: Session, product_id: int) -> bool:
    """Удаляет товар вместе со всей историей цен. True, если удалили."""
    product = get_product(db, product_id)
    if not product:
        return False
    # Сначала историю, потом сам товар — на случай, если внешний ключ
    # не настроен на каскад (в SQLite по умолчанию он не срабатывает).
    db.query(PriceHistory).filter(PriceHistory.product_id == product_id).delete()
    db.delete(product)
    db.commit()
    return True


def update_product_price(db: Session, product_id: int, new_price: float):
    """Обновляет текущую цену товара и дописывает точку в историю.
    Возвращает товар или None, если товара нет."""
    product = get_product(db, product_id)
    if not product:
        return None
    product.current_price = new_price
    db.add(PriceHistory(product_id=product_id, price=new_price))
    db.commit()
    db.refresh(product)
    return product
