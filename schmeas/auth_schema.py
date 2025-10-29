from pydantic import BaseModel, constr

class UserCreate(BaseModel):
    username: str = constr(min_length=3, max_length=50)
    password: str = constr(min_length=6, max_length=72)

class UserLogin(BaseModel):
    username: str
    password: str

class UserOut(BaseModel):
    id: int
    username: str
