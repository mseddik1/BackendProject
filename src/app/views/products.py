from math import degrees
from typing import List, Optional

from fastapi import APIRouter, Query, Depends
from sqlalchemy.orm import Session
from starlette import status

from src.app.services import services
from src.app.db.base import get_db
from src.app.schemas import schemas
from src.app.services import services
from src.app.models import dbmodels


products_router = APIRouter(prefix="/products", tags=["Products"])

@products_router.get("/", response_model=schemas.ProductListResponse)
def get_all_products(page:int = 1, per_page:int = 10, db:Session =Depends(get_db), _:dbmodels.User = Depends(services.get_current_active_user)):
    total, items = services.get_all_products(db, page, per_page)
    return {
        "page": page,
        "per_page": per_page,
        "total": total,
        "items": items
    }

@products_router.post("/", response_model=schemas.Product, status_code=status.HTTP_201_CREATED)
def create_product(product: schemas.ProductCreate,current_user:dbmodels.User = Depends(services.require_admin), db:Session = Depends(get_db)):
    return services.create_product(product, db, current_user)
# There was an issue here as the endpoint get has another path /{id}
# So when i added this /cursor under it i always got error as there was no id "cursor"
# thats why i removed it to be before the /{product_id} one
@products_router.get("/cursor", status_code=status.HTTP_200_OK)
def get_product_cursor(
        limit: int = Query(5, le=50),
        cursor: Optional[str] = None,
        db: Session = Depends(get_db)
):

    return services.get_products_cursor(limit, cursor, db)



@products_router.get("/{product_id}", response_model=schemas.Product)
def get_product_by_id(product_id:int, db:Session = Depends(get_db), _:dbmodels.User = Depends(services.get_current_active_user)):
    return services.get_product_by_id(product_id, db)

@products_router.get("/by-name/{name}", response_model=schemas.Product)
def get_product_by_name(name: str, db:Session = Depends(get_db), _:dbmodels.User = Depends(services.get_current_active_user)):
    return services.get_product_by_name(name, db)

@products_router.put("/{product_id}", response_model=schemas.Product)
def update_product(product_id:int, product: schemas.ProductUpdate, db: Session = Depends(get_db), current_user:dbmodels.User = Depends(services.require_admin)):
    return services.update_product(product_id, product, db, current_user)

@products_router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(product_id:int, db: Session = Depends(get_db), _:dbmodels.User = Depends(services.require_admin)):
    return services.delete_product(product_id, db)


@products_router.put("/publish/{product_id}")
def publish_product(product_id:int, db: Session = Depends(get_db), current_user:dbmodels.User = Depends(services.require_admin)):
    return services.publish_product(product_id, db)


