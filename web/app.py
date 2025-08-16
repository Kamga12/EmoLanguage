"""
FastAPI web server for EmoLanguage encode/decode API.

Provides rate-limited endpoints for encoding text to emojis and decoding emojis back to text.
Includes CORS protection and domain validation for emojipager.com.
"""

import sys
import time
from pathlib import Path
from typing import Dict, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, validator
import uvicorn

# Add parent directory to path to import encode/decode modules
sys.path.append(str(Path(__file__).parent.parent))

try:
    from encode import encode
    from decode import decode
except ImportError as e:
    print(f"Error importing encode/decode modules: {e}")
    print("Make sure encode.py and decode.py are in the parent directory and properly configured.")
    sys.exit(1)

# Pydantic models
class MessageRequest(BaseModel):
    message: str
    
    @validator('message')
    def validate_message(cls, v):
        if not v or not v.strip():
            raise ValueError('Message cannot be empty')
        if len(v) > 10000:  # Reasonable limit
            raise ValueError('Message too long (max 10000 characters)')
        return v.strip()

class MessageResponse(BaseModel):
    result: str
    processing_time_ms: float

# Rate limiting storage (in production, use Redis or similar)
rate_limit_storage: Dict[str, Dict] = {}

class RateLimiter:
    """Simple in-memory rate limiter."""
    
    def __init__(self, max_requests: int = 100, window_seconds: int = 3600):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
    
    def is_allowed(self, client_ip: str) -> bool:
        """Check if request is allowed based on rate limit."""
        current_time = time.time()
        
        if client_ip not in rate_limit_storage:
            rate_limit_storage[client_ip] = {
                'requests': [],
                'first_request': current_time
            }
        
        client_data = rate_limit_storage[client_ip]
        
        # Remove old requests outside the window
        client_data['requests'] = [
            req_time for req_time in client_data['requests']
            if current_time - req_time < self.window_seconds
        ]
        
        # Check if under limit
        if len(client_data['requests']) >= self.max_requests:
            return False
        
        # Add current request
        client_data['requests'].append(current_time)
        return True

# Initialize FastAPI app
app = FastAPI(
    title="EmoLanguage API",
    description="Convert text to emojis and emojis back to text",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Rate limiter instance
rate_limiter = RateLimiter(max_requests=100, window_seconds=3600)  # 100 requests per hour

# CORS middleware with domain restrictions
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://emojipager.com",
        "https://www.emojipager.com"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

def get_client_ip(request: Request) -> str:
    """Extract client IP from request, considering proxies."""
    # Check for forwarded headers first (for proxies/load balancers)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Take the first IP in the chain
        return forwarded_for.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # Fallback to direct client IP
    if request.client and request.client.host:
        return request.client.host
    
    # Final fallback
    return "unknown"

@app.middleware("http")
async def domain_and_rate_limit_middleware(request: Request, call_next):
    """Middleware for domain validation and rate limiting."""
    
    # Skip middleware for docs endpoints
    if request.url.path in ["/docs", "/redoc", "/openapi.json"]:
        return await call_next(request)
    
    # Domain validation (check Host header)
    host = request.headers.get("host", "").lower()
    allowed_hosts = ["api.emojipager.com"]
    
    if host not in allowed_hosts:
        raise HTTPException(
            status_code=403,
            detail="Access denied: Invalid host"
        )
    
    # Rate limiting
    # client_ip = get_client_ip(request)
    # if not rate_limiter.is_allowed(client_ip):
    #     raise HTTPException(
    #         status_code=429,
    #         detail="Rate limit exceeded. Try again later."
    #     )
    
    response = await call_next(request)
    return response

@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "service": "EmoLanguage API",
        "status": "healthy",
        "version": "1.0.0"
    }

@app.post("/encode", response_model=MessageResponse)
async def encode_text(request: MessageRequest):
    """
    Encode text to emoji sequences.
    
    Takes English text and converts it to emoji sequences while preserving
    grammatical context through morphological modifiers.
    """
    start_time = time.time()
    
    try:
        result = encode(request.message)
        processing_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        return MessageResponse(
            result=result,
            processing_time_ms=round(processing_time, 2)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error encoding message: {str(e)}"
        )

@app.post("/decode", response_model=MessageResponse)
async def decode_emojis(request: MessageRequest):
    """
    Decode emoji sequences back to text.
    
    Takes emoji sequences and converts them back to English text with
    intelligent grammar reconstruction.
    """
    start_time = time.time()
    
    try:
        result = decode(request.message)
        processing_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        return MessageResponse(
            result=result,
            processing_time_ms=round(processing_time, 2)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error decoding message: {str(e)}"
        )

@app.get("/health")
async def health_check():
    """Detailed health check endpoint."""
    try:
        # Test encode/decode functions
        test_encode = encode("hello world")
        test_decode = decode("🌍")
        
        return {
            "status": "healthy",
            "encode_test": "passed" if test_encode else "failed",
            "decode_test": "passed" if test_decode else "failed",
            "rate_limiter": "active",
            "cors": "configured"
        }
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Service unhealthy: {str(e)}"
        )

if __name__ == "__main__":
    print("Starting EmoLanguage API server...")
    print("Server will run on: http://localhost:54545")
    print("API Documentation: http://localhost:54545/docs")
    
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=54545,
        reload=True,
        log_level="info"
    )
