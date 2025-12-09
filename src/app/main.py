import threading

from fastapi import FastAPI

from src.app.workers import jobs
from src.app.views.auth import auth_router
from src.app.views.users import users_router
from src.app.views.products import products_router
from src.app.services import services



app = FastAPI(title="Integration with SQL!")
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(products_router)


@app.get("/")
def root() :
    return services.root()


@app.on_event("startup")
def start_background_workers():
    # Start the publish_product worker in a background thread
    t = threading.Thread(target=jobs.worker_loop, daemon=True)
    t.start()
    print("[MAIN] Background worker thread started")


