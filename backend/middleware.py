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
            body_bytes = await request.body()
            
            async def receive():
                return {"type": "http.request", "body": body_bytes}
            
            request._receive = receive
            
            response = await call_next(request)
            
            # Log after response to ensure it was processed
            try:
                db = await get_mongo_db()
                if db is not None:
                    user_id = "anonymous"
                    tenant_id = None
                    
                    # Extract tenant_id from X-Tenant-ID header
                    tenant_id_header = request.headers.get("X-Tenant-ID")
                    if tenant_id_header:
                        tenant_id = tenant_id_header
                    
                    # Try to get user from auth header if present
                    auth_header = request.headers.get("Authorization")
                    if auth_header and auth_header.startswith("Bearer "):
                        # In production, we would decode the JWT token here
                        # For now, we leave user_id as anonymous
                        pass

                    payload = None
                    if body_bytes:
                        try:
                            payload = json.loads(body_bytes)
                            # Sanitize sensitive fields
                            sensitive_fields = ["password", "password_hash", "otp_code", "token"]
                            for field in sensitive_fields:
                                if field in payload:
                                    payload[field] = "***"
                        except:
                            payload = str(body_bytes)[:500]  # Limit non-JSON payload size

                    log_entry = {
                        "timestamp": datetime.utcnow(),
                        "method": request.method,
                        "path": request.url.path,
                        "status_code": response.status_code,
                        "user_id": user_id,
                        "tenant_id": tenant_id,  # Added for multi-tenant isolation
                        "payload": payload,
                        "process_time": time.time() - start_time,
                        "client_ip": request.client.host if request.client else None,
                        "user_agent": request.headers.get("User-Agent", "unknown")[:200]
                    }
                    
                    await db["system_logs"].insert_one(log_entry)
            except Exception as e:
                print(f"Audit Log Error: {e}")
                
            return response
        else:
            return await call_next(request)
