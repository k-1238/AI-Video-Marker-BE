from fastapi import APIRouter

router = APIRouter(
    prefix="/example",
    tags=["Example"],
)

@router.get("/")
async def read_example():
    return { "message": "Hello, This Is An Example Route!" }
