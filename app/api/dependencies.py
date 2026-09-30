from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.models import ApiKey
from app.security.api_keys import hash_api_key


security = HTTPBearer()


def get_api_key(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> ApiKey:
    api_key_hash = hash_api_key(credentials.credentials)
    stmt = select(ApiKey).where(
        ApiKey.secret_hash == api_key_hash,
        ApiKey.is_active.is_(True),
    )
    api_key = db.execute(stmt).scalar_one_or_none()
    if api_key is None:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return api_key
