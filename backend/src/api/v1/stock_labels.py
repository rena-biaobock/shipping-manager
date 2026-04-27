from fastapi import APIRouter
from ...data.xlsx_loader import load_labels

router = APIRouter()


@router.get("/")
def list_stock_labels():
    return load_labels()
