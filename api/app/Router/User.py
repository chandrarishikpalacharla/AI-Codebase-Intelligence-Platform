from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.Scheme.user_schema import UserRequest
from app.Database.session import get_db
from app.Service.user_service import UserService

router = APIRouter(prefix="/api")

@router.post("/user")
def userpost(
    request: UserRequest,
    db: Session = Depends(get_db)
):
    return UserService.create_user(request, db)