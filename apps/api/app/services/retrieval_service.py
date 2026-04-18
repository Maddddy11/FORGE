from app.schemas.assets import AssetContextResponse
from app.services.store import store


class RetrievalService:
    def get_asset_context(self, asset_id: str) -> AssetContextResponse:
        linked_documents = [doc for doc in store.documents if doc.get("asset_id") == asset_id]
        return AssetContextResponse(asset_id=asset_id, linked_documents=linked_documents)
