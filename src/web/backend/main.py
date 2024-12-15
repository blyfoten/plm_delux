from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .logging_config import setup_logging

# Set up logging first thing
setup_logging()

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import routes after logging is configured
from .api import *  # noqa

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 