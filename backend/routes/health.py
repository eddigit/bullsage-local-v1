from fastapi import APIRouter

router = APIRouter(tags=["Health"])

@router.get("/")
async def root():
    return {"message": "BULL SAGE API is running"}

@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "BULL SAGE API",
        "version": "1.0.0"
    }
