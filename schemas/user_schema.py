from pydantic import BaseModel


class UserBase(BaseModel):
    email: str
    first_name: str
    last_name: str


class UserCreate(UserBase):
    password: str


class UserAuth(BaseModel):
    email: str
    password: str


class User(UserBase):
    id: int
    is_super: bool

    class Config:
        orm_mode = True


class UserAuthResponse(BaseModel):
    access_token: str
    token_type: str
    user: User

    # class Config:
    #     orm_mode = True

class SlackToken(BaseModel):
    slack_token: str
    channel_name: str


