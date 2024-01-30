import os
from datetime import datetime


from fastapi import APIRouter, HTTPException
from jose import jwt, JWTError
from starlette import status

import sys
sys.path.append("..")

router = APIRouter()


# Your api-key can be gotten from:  https://console.firebase.google.com/project/<project-name>/settings/cloudmessaging
# push_service = FCMNotification(api_key=os.environ.get("FCM_API_KEY"))
# DB에 따로 FCM 토큰을 저장하고 상대방이 접속중이 아닐 때는 DB에서 토큰을 받아와서 해당 사용자에게 푸시알림 실행하는 과정 시행


SECRET_KEY = os.environ["ACCESS_TOKEN_HASH"]
ALGORITHM = "HS256"


def get_current_user(token: str):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        account_id: str = payload.get("sub")
        if datetime.fromtimestamp(payload.get("exp")) < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if account_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    else:
        return int(account_id)


