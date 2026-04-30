from pydantic import BaseModel


class ProviderOut(BaseModel):
    code: str
    name: str
    status: str
    production_ready: bool = False
    capabilities: dict[str, bool] | None = None
    reason: str | None = None


class FeatureCapabilityOut(BaseModel):
    feature: str
    status: str
    reason: str | None = None
    providers: list[str]


class AudioCapabilitiesOut(BaseModel):
    features: list[FeatureCapabilityOut]
