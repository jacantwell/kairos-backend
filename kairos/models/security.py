from pydantic import BaseModel


# JSON payload containing tokens
class Tokens(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

# Contents of JWT token
class TokenPayload(BaseModel):
    sub: str
