import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.v1 import stock_labels, loads, bin_packing

app = FastAPI(title="Shipping Manager API", version="2.0.0")

_cors_origins = os.getenv(
    "CORS_ORIGINS", "http://localhost,http://localhost:4200"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

app.include_router(stock_labels.router, prefix="/web/api/v1/stock-labels")
app.include_router(loads.router, prefix="/web/api/v1/loads")
app.include_router(bin_packing.router, prefix="/web/api/v1/bin-packing")
