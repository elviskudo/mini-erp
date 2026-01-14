"""
Unit tests for Bank Reconciliation module.
Tests cover: get reconciliation data, mark transactions, list reconciliations

Runs against the live API server at localhost:8000
"""
import pytest
import httpx
import uuid


class TestBankReconciliation:
    """Tests for Bank Reconciliation endpoints."""
    
    @pytest.mark.asyncio
    async def test_get_reconciliation_data_returns_200(self, client: httpx.AsyncClient):
        """GET /finance/banking/reconciliation/{account_id} should return 200 with valid account."""
        # First get an account
        accounts_resp = await client.get("/finance/banking/accounts")
        assert accounts_resp.status_code == 200
        accounts = accounts_resp.json()
        
        if accounts:
            account_id = accounts[0]["id"]
            response = await client.get(f"/finance/banking/reconciliation/{account_id}")
            assert response.status_code == 200
            data = response.json()
            assert "book_balance" in data
            assert "transactions" in data
    
    @pytest.mark.asyncio
    async def test_get_reconciliation_not_found(self, client: httpx.AsyncClient):
        """GET /finance/banking/reconciliation/{id} with non-existent ID should return 404."""
        fake_id = str(uuid.uuid4())
        response = await client.get(f"/finance/banking/reconciliation/{fake_id}")
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_reconciliation_data_structure(self, client: httpx.AsyncClient):
        """Verify reconciliation data has expected fields."""
        accounts_resp = await client.get("/finance/banking/accounts")
        if accounts_resp.status_code == 200:
            accounts = accounts_resp.json()
            if accounts:
                account_id = accounts[0]["id"]
                response = await client.get(f"/finance/banking/reconciliation/{account_id}")
                assert response.status_code == 200
                data = response.json()
                
                assert "bank_account_id" in data
                assert "bank_account_name" in data
                assert "book_balance" in data
                assert "transactions" in data
                assert isinstance(data["transactions"], list)
    
    @pytest.mark.asyncio
    async def test_reconciliation_transactions_structure(self, client: httpx.AsyncClient):
        """Verify transaction items in reconciliation data have expected fields."""
        accounts_resp = await client.get("/finance/banking/accounts")
        if accounts_resp.status_code == 200:
            accounts = accounts_resp.json()
            if accounts:
                account_id = accounts[0]["id"]
                response = await client.get(f"/finance/banking/reconciliation/{account_id}")
                if response.status_code == 200:
                    transactions = response.json().get("transactions", [])
                    if transactions:
                        tx = transactions[0]
                        assert "id" in tx
                        assert "transaction_date" in tx
                        assert "amount" in tx
    
    @pytest.mark.asyncio
    async def test_mark_reconciled_empty_list(self, client: httpx.AsyncClient):
        """POST /finance/banking/reconciliation/mark with empty list should return 400."""
        response = await client.post("/finance/banking/reconciliation/mark", json={
            "transaction_ids": [],
            "statement_date": "2026-01-12"
        })
        assert response.status_code == 400
    
    @pytest.mark.asyncio
    async def test_mark_reconciled_invalid_ids(self, client: httpx.AsyncClient):
        """POST /finance/banking/reconciliation/mark with invalid IDs should handle gracefully."""
        fake_ids = [str(uuid.uuid4()), str(uuid.uuid4())]
        response = await client.post("/finance/banking/reconciliation/mark", json={
            "transaction_ids": fake_ids,
            "statement_date": "2026-01-12"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["reconciled_count"] == 0
    
    @pytest.mark.asyncio
    async def test_list_reconciliations_returns_200(self, client: httpx.AsyncClient):
        """GET /finance/banking/reconciliations should return 200 and list."""
        response = await client.get("/finance/banking/reconciliations")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    @pytest.mark.asyncio
    async def test_list_reconciliations_with_account_filter(self, client: httpx.AsyncClient):
        """GET /finance/banking/reconciliations with bank_account_id filter should work."""
        accounts_resp = await client.get("/finance/banking/accounts")
        if accounts_resp.status_code == 200:
            accounts = accounts_resp.json()
            if accounts:
                account_id = accounts[0]["id"]
                response = await client.get("/finance/banking/reconciliations", params={
                    "bank_account_id": account_id
                })
                assert response.status_code == 200


class TestReconciliationIntegration:
    """Integration tests for reconciliation workflow."""
    
    @pytest.mark.asyncio
    async def test_reconciliation_endpoint_accessible(self, client: httpx.AsyncClient):
        """Verify /finance/banking/reconciliations endpoint is registered."""
        response = await client.get("/finance/banking/reconciliations")
        assert response.status_code != 404
    
    @pytest.mark.asyncio
    async def test_mark_endpoint_accessible(self, client: httpx.AsyncClient):
        """Verify /finance/banking/reconciliation/mark endpoint is registered."""
        response = await client.post("/finance/banking/reconciliation/mark", json={
            "transaction_ids": [],
            "statement_date": "2026-01-12"
        })
        # 400 because empty list, but not 404
        assert response.status_code != 404
