"""FastAPI routing service for Kestrel Home Appliances."""
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.schemas import ServiceRequestInput, RoutingPredictionResponse
from app.model import KestrelRouter

app = FastAPI(
    title="Kestrel Service Request Router",
    description="Intelligent inbound routing for Kestrel service desk",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

router_instance = None


@app.on_event("startup")
def load_model():
    global router_instance
    try:
        router_instance = KestrelRouter('models/kestrel_router_pipeline.joblib')
        print("Model loaded successfully on startup.")
    except Exception as e:
        print(f"Warning: Model could not be loaded on startup: {e}")
        router_instance = None


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "model_loaded": router_instance is not None
    }


@app.post("/predict", response_model=RoutingPredictionResponse)
def predict_route(payload: ServiceRequestInput):
    global router_instance
    if router_instance is None:
        try:
            router_instance = KestrelRouter('models/kestrel_router_pipeline.joblib')
        except Exception as e:
            raise HTTPException(
                status_code=503,
                detail=f"Routing model artifact unavailable. Error: {str(e)}. Please run training first."
            )
    
    try:
        result = router_instance.predict_one(
            request_text=payload.request_text,
            product_family=payload.product_family,
            warranty_status=payload.warranty_status,
            channel=payload.channel,
            request_id=payload.request_id
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Inference error: {str(e)}"
        )


# Mount static directory for UI
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

    @app.get("/")
    def serve_ui():
        return FileResponse(os.path.join(static_dir, "index.html"))
