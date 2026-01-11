"""
Test configuration and fixtures for backend tests.
Uses httpx to test against running API server.
"""
import pytest
import httpx
from typing import AsyncGenerator
import uuid


# Base URL for API testing - assumes API is running at localhost:8000
API_BASE_URL = "http://localhost:8000"

# Default test tenant ID (matches DEFAULT_TENANT_ID in routers)
TEST_TENANT_ID = uuid.UUID("6c812e6d-da95-49e8-8510-cc36b196bdb6")


@pytest.fixture
async def client() -> AsyncGenerator[httpx.AsyncClient, None]:
    """Get an async HTTP client for testing against running API."""
    async with httpx.AsyncClient(base_url=API_BASE_URL, timeout=30.0) as ac:
        yield ac


@pytest.fixture
def sample_vendor_data():
    """Sample vendor data for testing."""
    return {
        "code": f"VENDOR-{uuid.uuid4().hex[:6].upper()}",
        "name": "Test Vendor Supplier",
        "tax_id": "12.345.678.9-012.000",
        "email": "vendor@test.com",
        "phone": "021-1234567",
        "address": "Jl. Test No. 123"
    }


@pytest.fixture
def sample_bill_data():
    """Sample vendor bill data for testing."""
    return {
        "vendor_id": str(uuid.uuid4()),
        "invoice_number": f"INV-TEST-{uuid.uuid4().hex[:8].upper()}",
        "date": "2026-01-10",
        "due_date": "2026-02-10",
        "payment_terms": "Net 30",
        "subtotal": 1000000,
        "tax_amount": 110000,
        "total_amount": 1110000,
        "notes": "Test bill"
    }


@pytest.fixture
def sample_payment_data():
    """Sample AP payment data for testing."""
    return {
        "vendor_id": str(uuid.uuid4()),
        "payment_date": "2026-01-10",
        "payment_method": "Bank Transfer",
        "amount": 500000,
        "reference_number": f"TRF-{uuid.uuid4().hex[:6].upper()}",
        "notes": "Test payment"
    }
