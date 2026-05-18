from typing import Dict, Any
from app.schemas.portfolio import PortfolioReconstructResponse

class TimelineRenderer:
    def render_to_response(self, raw_data: Dict[str, Any]) -> PortfolioReconstructResponse:
        """
        Converts raw timeline generator data dictionary into the validated Pydantic model.
        """
        return PortfolioReconstructResponse(**raw_data)
        
    def render_to_dict(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validates the raw data dictionary and returns it as a validated dict response.
        """
        response = self.render_to_response(raw_data)
        return response.model_dump(mode="json")
