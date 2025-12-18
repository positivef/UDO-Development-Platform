"""Direct endpoint test with better error output"""
import sys
import os
import asyncio
from uuid import uuid4

# Add parent directory to path for src module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import models
from backend.app.models.uncertainty_time_integration import UncertaintyAwareTrackingRequest
from backend.app.models.time_tracking import TaskType, Phase, AIModel

# Import the router function
from backend.app.routers.uncertainty import start_uncertainty_aware_tracking

# Import dependencies
from src.uncertainty_map_v3 import UncertaintyMap

async def test_endpoint():
    """Test the endpoint directly"""
    try:
        # Create request
        request = UncertaintyAwareTrackingRequest(
            task_id="test_integration_001",
            task_type=TaskType.IMPLEMENTATION,
            phase=Phase.IMPLEMENTATION,
            ai_used=AIModel.CLAUDE,
            uncertainty_context={
                "phase": "implementation",
                "has_code": True,
                "validation_score": 0.7,
                "team_size": 3,
                "timeline_weeks": 8
            },
            metadata={"test": "uncertainty_integration"}
        )

        # Create uncertainty map
        uncertainty_map = UncertaintyMap(
            project_name="UDO-Dashboard",
            use_ml_models=False
        )

        # Call the endpoint
        print("Calling endpoint...")
        response = await start_uncertainty_aware_tracking(request, uncertainty_map)

        print("[OK] Success!")
        print(f"Session ID: {response.session_id}")
        print(f"Standard Baseline: {response.baseline_seconds}s")
        print(f"Adjusted Baseline: {response.adjusted_baseline_seconds}s")
        print(f"Uncertainty State: {response.uncertainty_state}")
        print(f"Confidence Score: {response.confidence_score:.2%}")
        print(f"Risk Factors: {response.risk_factors}")

    except Exception as e:
        print(f"[FAIL] Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_endpoint())
