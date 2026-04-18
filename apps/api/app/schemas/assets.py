from pydantic import BaseModel


class AssetContextResponse(BaseModel):
    asset_id: str
    linked_documents: list[dict]
