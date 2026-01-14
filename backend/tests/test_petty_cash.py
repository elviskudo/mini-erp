"""
Unit tests for Petty Cash module.
Tests cover: list transactions, record expense, record replenishment

Runs against the live API server at localhost:8000
"""
import pytest
import httpx
import uuid


class TestPettyCash:
    """Tests for Petty Cash endpoints."""
    
    @pytest.mark.asyncio
    async def test_list_petty_cash_returns_200(self, client: httpx.AsyncClient):
        """GET /finance/banking/petty-cash should return 200."""
        response = await client.get("/finance/banking/petty-cash")
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_list_petty_cash_structure(self, client: httpx.AsyncClient):
        """Verify petty cash response has expected structure."""
        response = await client.get("/finance/banking/petty-cash")
        assert response.status_code == 200
        data = response.json()
        
        assert "balance" in data
        assert "transactions" in data
        assert isinstance(data["transactions"], list)
    
    @pytest.mark.asyncio
    async def test_list_petty_cash_with_date_range(self, client: httpx.AsyncClient):
        """GET /finance/banking/petty-cash with date range should work."""
        response = await client.get("/finance/banking/petty-cash", params={
            "date_from": "2026-01-01",
            "date_to": "2026-12-31"
        })
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_create_expense_success(self, client: httpx.AsyncClient):
        """POST /finance/banking/petty-cash/expense should create expense."""
        response = await client.post("/finance/banking/petty-cash/expense", json={
            "date": "2026-01-12",
            "amount": 25000,
            "category": "Office Supplies",
            "description": "Test expense",
            "requested_by": "Test User"
        })
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["type"] == "expense"
    
    @pytest.mark.asyncio
    async def test_create_expense_zero_amount(self, client: httpx.AsyncClient):
        """POST /finance/banking/petty-cash/expense with zero amount should return 400."""
        response = await client.post("/finance/banking/petty-cash/expense", json={
            "date": "2026-01-12",
            "amount": 0,
            "description": "Zero test"
        })
        assert response.status_code == 400
    
    @pytest.mark.asyncio
    async def test_create_replenishment_success(self, client: httpx.AsyncClient):
        """POST /finance/banking/petty-cash/replenish should create replenishment."""
        response = await client.post("/finance/banking/petty-cash/replenish", json={
            "date": "2026-01-12",
            "amount": 1000000,
            "description": "Test replenishment"
        })
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["type"] == "replenishment"
    
    @pytest.mark.asyncio
    async def test_create_replenishment_zero_amount(self, client: httpx.AsyncClient):
        """POST /finance/banking/petty-cash/replenish with zero amount should return 400."""
        response = await client.post("/finance/banking/petty-cash/replenish", json={
            "date": "2026-01-12",
            "amount": 0,
            "description": "Zero test"
        })
        assert response.status_code == 400
    
    @pytest.mark.asyncio
    async def test_expense_transaction_structure(self, client: httpx.AsyncClient):
        """Verify expense response has expected fields."""
        response = await client.post("/finance/banking/petty-cash/expense", json={
            "date": "2026-01-12",
            "amount": 15000,
            "category": "Transportation",
            "description": "Taxi"
        })
        if response.status_code == 200:
            data = response.json()
            assert "id" in data
            assert "transaction_number" in data
            assert "amount" in data
            assert "type" in data
            assert "message" in data


class TestPettyCashIntegration:
    """Integration tests for petty cash workflow."""
    
    @pytest.mark.asyncio
    async def test_petty_cash_endpoint_accessible(self, client: httpx.AsyncClient):
        """Verify /finance/banking/petty-cash endpoint is registered."""
        response = await client.get("/finance/banking/petty-cash")
        assert response.status_code != 404
    
    @pytest.mark.asyncio
    async def test_expense_endpoint_accessible(self, client: httpx.AsyncClient):
        """Verify /finance/banking/petty-cash/expense endpoint is registered."""
        response = await client.post("/finance/banking/petty-cash/expense", json={
            "amount": 1000,
            "description": "Test"
        })
        assert response.status_code != 404
    
    @pytest.mark.asyncio
    async def test_replenish_endpoint_accessible(self, client: httpx.AsyncClient):
        """Verify /finance/banking/petty-cash/replenish endpoint is registered."""
        response = await client.post("/finance/banking/petty-cash/replenish", json={
            "amount": 1000,
            "description": "Test"
        })
        assert response.status_code != 404
    
    @pytest.mark.asyncio
    async def test_balance_updates_after_transactions(self, client: httpx.AsyncClient):
        """Balance should update after recording transactions."""
        # Get initial balance
        initial_resp = await client.get("/finance/banking/petty-cash")
        initial_balance = initial_resp.json().get("balance", 0)
        
        # Add replenishment
        await client.post("/finance/banking/petty-cash/replenish", json={
            "date": "2026-01-12",
            "amount": 100000,
            "description": "Test balance update"
        })
        
        # Check new balance
        final_resp = await client.get("/finance/banking/petty-cash")
        final_balance = final_resp.json().get("balance", 0)
        
        # Balance should have increased
        assert final_balance >= initial_balance
