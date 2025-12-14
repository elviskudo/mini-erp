from fastapi import HTTPException
from sqlalchemy.future import select

async def get_object_or_404(db, model, id):
    result = await db.execute(select(model).where(model.id == id))
    obj = result.scalar_one_or_none()
    if not obj:
        raise HTTPException(status_code=404, detail=f"{model.__name__} not found")
    return obj
