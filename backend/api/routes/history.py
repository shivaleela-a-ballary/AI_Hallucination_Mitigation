from fastapi import APIRouter

router = APIRouter(tags=["History"])


@router.get("/history")
def history():
    return {
        "history": []
    }