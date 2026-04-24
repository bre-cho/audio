from pydantic import BaseModel


class ProviderOut(BaseModel):
    code: str
    name: str
    status: str
