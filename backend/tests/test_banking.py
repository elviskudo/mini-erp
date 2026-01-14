"""
Unit tests for Banking/Finance module.
Tests cover: Bank Accounts, Bank Transactions

Runs against the live API server at localhost:8000
"""
import pytest
import httpx
import uuid


class TestBankAccounts:
    """Tests for Bank Accounts endpoints."""
    
    @pytest.mark.asyncio
    async def test_list_bank_accounts_returns_200(self, client: httpx.AsyncClient):
        """GET /finance/banking/accounts should return 200 and list."""
        response = await client.get("/finance/banking/accounts")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    @pytest.mark.asyncio
    async def test_bank_account_response_structure(self, client: httpx.AsyncClient):
        """Verify bank account response has expected fields."""
        response = await client.get("/finance/banking/accounts")
        assert response.status_code == 200
        accounts = response.json()
        
        if accounts:
            account = accounts[0]
            assert "id" in account
            assert "code" in account
            assert "name" in account
            assert "bank_name" in account
            assert "current_balance" in account
    
    @pytest.mark.asyncio
    async def test_get_bank_account_not_found(self, client: httpx.AsyncClient):
        """GET /finance/banking/accounts/{id} with non-existent ID should return 404."""
        fake_id = str(uuid.uuid4())
        response = await client.get(f"/finance/banking/accounts/{fake_id}")
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_create_bank_account_missing_fields(self, client: httpx.AsyncClient):
        """POST /finance/banking/accounts without required fields should return 422."""
        response = await client.post("/finance/banking/accounts", json={})
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_update_bank_account_not_found(self, client: httpx.AsyncClient):
        """PUT /finance/banking/accounts/{id} with non-existent ID should return 404."""
        fake_id = str(uuid.uuid4())
        response = await client.put(f"/finance/banking/accounts/{fake_id}", json={
            "name": "Updated Account"
        })
        assert response.status_code == 404


class TestBankTransactions:
    """Tests for Bank Transactions endpoints."""
    
    @pytest.mark.asyncio
    async def test_list_transactions_returns_200(self, client: httpx.AsyncClient):
        """GET /finance/banking/transactions should return 200 and list."""
        response = await client.get("/finance/banking/transactions")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    @pytest.mark.asyncio
    async def test_list_transactions_with_filters(self, client: httpx.AsyncClient):
        """GET /finance/banking/transactions with query params should work."""
        response = await client.get("/finance/banking/transactions", params={
            "skip": 0,
            "limit": 10
        })
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    @pytest.mark.asyncio
    async def test_list_transactions_with_date_range(self, client: httpx.AsyncClient):
        """GET /finance/banking/transactions with date range should work."""
        response = await client.get("/finance/banking/transactions", params={
            "date_from": "2026-01-01",
            "date_to": "2026-12-31"
        })
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    @pytest.mark.asyncio
    async def test_get_transaction_not_found(self, client: httpx.AsyncClient):
        """GET /finance/banking/transactions/{id} with non-existent ID should return 404."""
        fake_id = str(uuid.uuid4())
        response = await client.get(f"/finance/banking/transactions/{fake_id}")
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_create_transaction_missing_account_returns_422(self, client: httpx.AsyncClient):
        """POST /finance/banking/transactions without bank_account_id should return 422."""
        response = await client.post("/finance/banking/transactions", json={
            "transaction_date": "2026-01-10",
            "transaction_type": "deposit",
            "amount": 1000000
        })
        # Pydantic validation returns 422 for missing required field
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_create_transaction_invalid_account(self, client: httpx.AsyncClient):
        """POST /finance/banking/transactions with non-existent account should return 404."""
        fake_account_id = str(uuid.uuid4())
        response = await client.post("/finance/banking/transactions", json={
            "bank_account_id": fake_account_id,
            "transaction_date": "2026-01-10",
            "transaction_type": "deposit",
            "amount": 1000000
        })
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_transaction_response_structure(self, client: httpx.AsyncClient):
        """Verify transaction response has expected fields."""
        response = await client.get("/finance/banking/transactions")
        assert response.status_code == 200
        transactions = response.json()
        
        if transactions:
            transaction = transactions[0]
            assert "id" in transaction
            assert "transaction_number" in transaction
            assert "amount" in transaction
            assert "transaction_type" in transaction


class TestBankingIntegration:
    """Integration tests for Banking workflow."""
    
    @pytest.mark.asyncio
    async def test_accounts_endpoint_accessible(self, client: httpx.AsyncClient):
        """Verify /finance/banking/accounts endpoint is registered."""
        response = await client.get("/finance/banking/accounts")
        assert response.status_code != 404
    
    @pytest.mark.asyncio
    async def test_transactions_endpoint_accessible(self, client: httpx.AsyncClient):
        """Verify /finance/banking/transactions endpoint is registered."""
        response = await client.get("/finance/banking/transactions")
        assert response.status_code != 404
    
    @pytest.mark.asyncio
    async def test_transaction_pagination_limits(self, client: httpx.AsyncClient):
        """Test pagination parameters work correctly."""
        response = await client.get("/finance/banking/transactions", params={"skip": 0, "limit": 5})
        assert response.status_code == 200
        transactions = response.json()
        assert len(transactions) <= 5
