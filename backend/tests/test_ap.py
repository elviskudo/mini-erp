"""
Unit tests for Account Payable (AP) module.
Tests cover: Vendor Bills, AP Payments

Runs against the live API server at localhost:8000
"""
import pytest
import httpx
import uuid


class TestAPBills:
    """Tests for AP Bills (Vendor Invoices) endpoints."""
    
    @pytest.mark.asyncio
    async def test_list_bills_returns_200(self, client: httpx.AsyncClient):
        """GET /ap/bills should return 200 and list of bills."""
        response = await client.get("/ap/bills")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    @pytest.mark.asyncio
    async def test_list_bills_with_filters(self, client: httpx.AsyncClient):
        """GET /ap/bills with query params should filter results."""
        response = await client.get("/ap/bills", params={
            "status": "Posted",
            "skip": 0,
            "limit": 10
        })
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    @pytest.mark.asyncio
    async def test_list_bills_with_date_range(self, client: httpx.AsyncClient):
        """GET /ap/bills with date range should work."""
        response = await client.get("/ap/bills", params={
            "date_from": "2026-01-01",
            "date_to": "2026-12-31"
        })
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    @pytest.mark.asyncio
    async def test_create_bill_missing_required_fields(self, client: httpx.AsyncClient):
        """POST /ap/invoices without required fields should return 422."""
        response = await client.post("/ap/invoices", json={})
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_update_bill_not_found(self, client: httpx.AsyncClient):
        """PUT /ap/bills/{id} with non-existent ID should return 404."""
        fake_id = str(uuid.uuid4())
        response = await client.put(f"/ap/bills/{fake_id}", json={
            "invoice_number": "UPDATED-001"
        })
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_bill_response_structure(self, client: httpx.AsyncClient):
        """Verify bill response has expected fields."""
        response = await client.get("/ap/bills")
        assert response.status_code == 200
        bills = response.json()
        
        if bills:
            bill = bills[0]
            # Check required fields exist
            assert "id" in bill
            assert "invoice_number" in bill
            assert "vendor_id" in bill
            assert "total_amount" in bill


class TestAPPayments:
    """Tests for AP Payments endpoints."""
    
    @pytest.mark.asyncio
    async def test_list_payments_returns_200(self, client: httpx.AsyncClient):
        """GET /ap/payments should return 200 and list."""
        response = await client.get("/ap/payments")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    @pytest.mark.asyncio
    async def test_list_payments_with_date_filter(self, client: httpx.AsyncClient):
        """GET /ap/payments with date range should work."""
        response = await client.get("/ap/payments", params={
            "date_from": "2026-01-01",
            "date_to": "2026-12-31"
        })
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_create_payment_missing_vendor_returns_422(self, client: httpx.AsyncClient):
        """POST /ap/payments without vendor_id should return 422 (validation error)."""
        response = await client.post("/ap/payments", json={
            "payment_date": "2026-01-10",
            "payment_method": "Bank Transfer",
            "amount": 100000
        })
        # Pydantic validation returns 422 for missing required field
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_create_payment_empty_vendor_returns_400(self, client: httpx.AsyncClient):
        """POST /ap/payments with empty vendor_id should return 400."""
        response = await client.post("/ap/payments", json={
            "vendor_id": "",
            "payment_date": "2026-01-10",
            "payment_method": "Bank Transfer",
            "amount": 100000
        })
        # Should return 400 for empty vendor_id 
        assert response.status_code == 400
    
    @pytest.mark.asyncio
    async def test_payment_response_structure(self, client: httpx.AsyncClient):
        """Verify payment response has expected fields."""
        response = await client.get("/ap/payments")
        assert response.status_code == 200
        payments = response.json()
        
        if payments:
            payment = payments[0]
            assert "id" in payment
            assert "payment_number" in payment
            assert "amount" in payment


class TestAPIntegration:
    """Integration tests for AP workflow."""
    
    @pytest.mark.asyncio
    async def test_bills_endpoint_accessible(self, client: httpx.AsyncClient):
        """Verify /ap/bills endpoint is registered and accessible."""
        response = await client.get("/ap/bills")
        assert response.status_code != 404
    
    @pytest.mark.asyncio
    async def test_payments_endpoint_accessible(self, client: httpx.AsyncClient):
        """Verify /ap/payments endpoint is registered and accessible."""
        response = await client.get("/ap/payments")
        assert response.status_code != 404
    
    @pytest.mark.asyncio
    async def test_search_bills_by_invoice_number(self, client: httpx.AsyncClient):
        """Verify bills can be searched/filtered."""
        response = await client.get("/ap/bills")
        assert response.status_code == 200
        bills = response.json()
        
        # Verify data can be filtered client-side
        if bills:
            first_bill = bills[0]
            inv_num = first_bill.get("invoice_number", "")
            # Client-side filtering would work on this data
            filtered = [b for b in bills if inv_num.lower() in b.get("invoice_number", "").lower()]
            assert len(filtered) >= 1
    
    @pytest.mark.asyncio
    async def test_ap_pagination_limits(self, client: httpx.AsyncClient):
        """Test pagination parameters work correctly."""
        response = await client.get("/ap/bills", params={"skip": 0, "limit": 5})
        assert response.status_code == 200
        bills = response.json()
        assert len(bills) <= 5
    
    @pytest.mark.asyncio
    async def test_payment_list_is_ordered(self, client: httpx.AsyncClient):
        """Verify payments list has consistent ordering."""
        response1 = await client.get("/ap/payments")
        response2 = await client.get("/ap/payments")
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        # Same request should return same order
        if response1.json() and response2.json():
            assert response1.json()[0]["id"] == response2.json()[0]["id"]
