from pydantic import BaseModel

class LabDataPayload(BaseModel):
    device_id: str
    parameter: str # e.g., "weight", "ph", "spectro"
    value: float
    unit: str
    timestamp: str
