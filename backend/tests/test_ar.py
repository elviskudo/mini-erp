"""
Unit tests for Account Receivable (AR) module.
Tests cover: Customers, Invoices, Receipts, Aging Report

Runs against the live API server at localhost:8000
"""
import pytest
import httpx
import uuid


class TestARCustomers:
    """Tests for AR Customers endpoints."""
    
    @pytest.mark.asyncio
    async def test_list_customers_returns_200(self, client: httpx.AsyncClient):
        """GET /ar/customers should return 200 and list."""
        response = await client.get("/ar/customers")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    @pytest.mark.asyncio
    async def test_customer_response_structure(self, client: httpx.AsyncClient):
        """Verify customer response has expected fields."""
        response = await client.get("/ar/customers")
        assert response.status_code == 200
        customers = response.json()
        
        if customers:
            customer = customers[0]
            assert "id" in customer
            assert "name" in customer


class TestARInvoices:
    """Tests for AR Invoices endpoints."""
    
    @pytest.mark.asyncio
    async def test_list_invoices_returns_200(self, client: httpx.AsyncClient):
        """GET /ar/invoices should return 200 and list."""
        response = await client.get("/ar/invoices")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    @pytest.mark.asyncio
    async def test_list_invoices_with_filters(self, client: httpx.AsyncClient):
        """GET /ar/invoices with query params should work."""
        response = await client.get("/ar/invoices", params={
            "status": "Posted",
            "skip": 0,
            "limit": 10
        })
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    @pytest.mark.asyncio
    async def test_list_invoices_with_date_range(self, client: httpx.AsyncClient):
        """GET /ar/invoices with date range should work."""
        response = await client.get("/ar/invoices", params={
            "date_from": "2026-01-01",
            "date_to": "2026-12-31"
        })
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    @pytest.mark.asyncio
    async def test_create_invoice_missing_required_fields(self, client: httpx.AsyncClient):
        """POST /ar/invoices without required fields should return 422."""
        response = await client.post("/ar/invoices", json={})
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_get_invoice_not_found(self, client: httpx.AsyncClient):
        """GET /ar/invoices/{id} with non-existent ID should return 404."""
        fake_id = str(uuid.uuid4())
        response = await client.get(f"/ar/invoices/{fake_id}")
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_update_invoice_not_found(self, client: httpx.AsyncClient):
        """PUT /ar/invoices/{id} with non-existent ID should return 404."""
        fake_id = str(uuid.uuid4())
        response = await client.put(f"/ar/invoices/{fake_id}", json={
            "customer_id": str(uuid.uuid4()),
            "items": []
        })
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_delete_invoice_not_found(self, client: httpx.AsyncClient):
        """DELETE /ar/invoices/{id} with non-existent ID should return 404."""
        fake_id = str(uuid.uuid4())
        response = await client.delete(f"/ar/invoices/{fake_id}")
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_invoice_response_structure(self, client: httpx.AsyncClient):
        """Verify invoice response has expected fields."""
        response = await client.get("/ar/invoices")
        assert response.status_code == 200
        invoices = response.json()
        
        if invoices:
            invoice = invoices[0]
            assert "id" in invoice
            assert "invoice_number" in invoice
            assert "customer_id" in invoice
            assert "total_amount" in invoice


class TestARReceipts:
    """Tests for AR Receipts/Payments endpoints."""
    
    @pytest.mark.asyncio
    async def test_list_receipts_returns_200(self, client: httpx.AsyncClient):
        """GET /ar/receipts should return 200 and list."""
        response = await client.get("/ar/receipts")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    @pytest.mark.asyncio
    async def test_list_receipts_with_date_filter(self, client: httpx.AsyncClient):
        """GET /ar/receipts with date range should work."""
        response = await client.get("/ar/receipts", params={
            "date_from": "2026-01-01",
            "date_to": "2026-12-31"
        })
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_create_receipt_missing_customer_returns_422(self, client: httpx.AsyncClient):
        """POST /ar/receipts without customer_id should return 422 (validation error)."""
        response = await client.post("/ar/receipts", json={
            "payment_date": "2026-01-10",
            "payment_method": "Bank Transfer",
            "amount": 100000
        })
        # Pydantic validation returns 422 for missing required field
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_create_receipt_invalid_customer(self, client: httpx.AsyncClient):
        """POST /ar/receipts with non-existent customer should return 404."""
        fake_customer_id = str(uuid.uuid4())
        response = await client.post("/ar/receipts", json={
            "customer_id": fake_customer_id,
            "payment_date": "2026-01-10",
            "payment_method": "Bank Transfer",
            "amount": 100000
        })
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_receipt_response_structure(self, client: httpx.AsyncClient):
        """Verify receipt response has expected fields."""
        response = await client.get("/ar/receipts")
        assert response.status_code == 200
        receipts = response.json()
        
        if receipts:
            receipt = receipts[0]
            assert "id" in receipt
            assert "receipt_number" in receipt
            assert "amount" in receipt


class TestARAgingReport:
    """Tests for AR Aging Report endpoint."""
    
    @pytest.mark.asyncio
    async def test_aging_report_returns_200(self, client: httpx.AsyncClient):
        """GET /ar/aging should return 200."""
        response = await client.get("/ar/aging")
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_aging_report_structure(self, client: httpx.AsyncClient):
        """Verify aging report has expected structure."""
        response = await client.get("/ar/aging")
        assert response.status_code == 200
        data = response.json()
        
        # Check required fields
        assert "buckets" in data
        assert "customers" in data
        assert "total" in data
        
        # Verify buckets is list with 5 items
        assert isinstance(data["buckets"], list)
        assert len(data["buckets"]) == 5
        
        # Verify each bucket has label, amount, count
        for bucket in data["buckets"]:
            assert "label" in bucket
            assert "amount" in bucket
            assert "count" in bucket
    
    @pytest.mark.asyncio
    async def test_aging_report_with_date(self, client: httpx.AsyncClient):
        """GET /ar/aging with as_of_date should work."""
        response = await client.get("/ar/aging", params={
            "as_of_date": "2026-01-10"
        })
        assert response.status_code == 200
        data = response.json()
        assert "as_of_date" in data
    
    @pytest.mark.asyncio
    async def test_aging_buckets_labels(self, client: httpx.AsyncClient):
        """Verify bucket labels are correct."""
        response = await client.get("/ar/aging")
        assert response.status_code == 200
        buckets = response.json()["buckets"]
        
        expected_labels = ["Current", "1-30 Days", "31-60 Days", "61-90 Days", "> 90 Days"]
        actual_labels = [b["label"] for b in buckets]
        assert actual_labels == expected_labels
    
    @pytest.mark.asyncio
    async def test_aging_customer_breakdown(self, client: httpx.AsyncClient):
        """Verify customer breakdown structure."""
        response = await client.get("/ar/aging")
        assert response.status_code == 200
        customers = response.json()["customers"]
        
        if customers:
            customer = customers[0]
            # Check expected fields in customer breakdown
            assert "customer" in customer
            assert "current" in customer
            assert "days_1_30" in customer
            assert "days_31_60" in customer
            assert "days_61_90" in customer
            assert "over_90" in customer
            assert "total" in customer


class TestARIntegration:
    """Integration tests for AR workflow."""
    
    @pytest.mark.asyncio
    async def test_invoices_endpoint_accessible(self, client: httpx.AsyncClient):
        """Verify /ar/invoices endpoint is registered."""
        response = await client.get("/ar/invoices")
        assert response.status_code != 404
    
    @pytest.mark.asyncio
    async def test_receipts_endpoint_accessible(self, client: httpx.AsyncClient):
        """Verify /ar/receipts endpoint is registered."""
        response = await client.get("/ar/receipts")
        assert response.status_code != 404
    
    @pytest.mark.asyncio
    async def test_aging_endpoint_accessible(self, client: httpx.AsyncClient):
        """Verify /ar/aging endpoint is registered."""
        response = await client.get("/ar/aging")
        assert response.status_code != 404
    
    @pytest.mark.asyncio
    async def test_ar_pagination_limits(self, client: httpx.AsyncClient):
        """Test pagination parameters work correctly."""
        response = await client.get("/ar/invoices", params={"skip": 0, "limit": 5})
        assert response.status_code == 200
        invoices = response.json()
        assert len(invoices) <= 5
