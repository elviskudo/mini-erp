from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
from connections.mongodb import get_mongo_db
import time
import json
from datetime import datetime

class AuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.method in ["POST", "PUT", "DELETE", "PATCH"]:
            start_time = time.time()
            
            # Clone request body because consuming it makes it unavailable for the actual handler
            # Starlette/FastAPI request body is a stream. 
            # Ideally we should use a dependency or read/write approach, but for middleware it's tricky.
            # A common pattern is to read, store, and replace receive.
            
            body_bytes = await request.body()
            
            async def receive():
                return {"type": "http.request", "body": body_bytes}
            
            request._receive = receive
            
            response = await call_next(request)
            
            # Log after response to ensure it was processed (or attempted)
            # We can run this in background task to not block response
            
            try:
                db = await get_mongo_db()
                if db is not None:
                    user_id = "anonymous"
                    # Try to get user from auth header if present (simplified parsing)
                    auth_header = request.headers.get("Authorization")
                    if auth_header and auth_header.startswith("Bearer "):
                         # In real app, we might decode token here or rely on request state if set by prev middleware
                         pass

                    payload = None
                    if body_bytes:
                        try:
                            payload = json.loads(body_bytes)
                            # Basic sanitization
                            if "password" in payload:
                                payload["password"] = "***"
                        except:
                            payload = str(body_bytes)

                    log_entry = {
                        "timestamp": datetime.utcnow(),
                        "method": request.method,
                        "path": request.url.path,
                        "status_code": response.status_code,
                        "user_id": user_id, 
                        "payload": payload,
                        "process_time": time.time() - start_time
                    }
                    
                    await db["system_logs"].insert_one(log_entry)
            except Exception as e:
                print(f"Audit Log Error: {e}")
                
            return response
        else:
            return await call_next(request)
