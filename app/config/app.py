from api import router
from config.settings import settings
from config.setup import setup
from fastapi import FastAPI

app = FastAPI(
    debug=settings.DEBUG,
    title="rent-crm",
    redirect_slashes=False,
    docs_url=None,
    redoc_url=None,
)
app.include_router(router)

setup(app=app)
