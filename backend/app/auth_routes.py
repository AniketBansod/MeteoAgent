from fastapi import APIRouter, HTTPException
from app.schemas import SignupRequest, SignupResponse
from app.db import get_db_connection
from app.security import hash_password
from app.security import verify_password, create_access_token
from app.schemas import LoginRequest, LoginResponse
from fastapi import Depends
from app.security import get_current_user_id
router = APIRouter(prefix="/auth", tags=["auth"])
@router.post("/login", response_model=LoginResponse)
def login(req: LoginRequest):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT id, password_hash FROM users WHERE email = %s",
        (req.email,)
    )
    row = cur.fetchone()

    cur.close()
    conn.close()

    if not row:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    user_id, pw_hash = row

    if not verify_password(req.password, pw_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(user_id)

    return LoginResponse(access_token=token)

@router.get("/me")
def whoami(user_id: int = Depends(get_current_user_id)):
    return {"user_id": user_id}
@router.post("/signup", response_model=SignupResponse)
def signup(req: SignupRequest):
    conn = get_db_connection()
    cur = conn.cursor()

    # check existing
    cur.execute("SELECT id FROM users WHERE email = %s", (req.email,))
    if cur.fetchone():
        cur.close()
        conn.close()
        raise HTTPException(status_code=400, detail="Email already registered")

    pw_hash = hash_password(req.password)

    cur.execute(
        "INSERT INTO users (email, password_hash) VALUES (%s, %s) RETURNING id",
        (req.email, pw_hash),
    )
    user_id = cur.fetchone()[0]

    conn.commit()
    cur.close()
    conn.close()

    return SignupResponse(user_id=user_id, email=req.email)
