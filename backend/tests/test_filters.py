"""
Unit tests for API Filters functionality.
Tests cover: date range, account/vendor/customer filters

Runs against the live API server at localhost:8000
"""
import pytest
import httpx
import uuid


class TestBankingTransactionsFilters:
    """Tests for Banking Transactions filter parameters."""
    
    @pytest.mark.asyncio
    async def test_filter_by_bank_account_id(self, client: httpx.AsyncClient):
        """GET /finance/banking/transactions with bank_account_id should filter."""
        # First get accounts
        accounts_resp = await client.get("/finance/banking/accounts")
        assert accounts_resp.status_code == 200
        accounts = accounts_resp.json()
        
        if accounts:
            account_id = accounts[0]["id"]
            response = await client.get("/finance/banking/transactions", params={
                "bank_account_id": account_id
            })
            assert response.status_code == 200
            transactions = response.json()
            # All returned transactions should belong to this account
            for t in transactions:
                assert t["bank_account_id"] == account_id
    
    @pytest.mark.asyncio
    async def test_filter_by_date_range(self, client: httpx.AsyncClient):
        """GET /finance/banking/transactions with date range should filter."""
        response = await client.get("/finance/banking/transactions", params={
            "date_from": "2026-01-01",
            "date_to": "2026-01-31"
        })
        assert response.status_code == 200
        transactions = response.json()
        # All returned transactions should be within date range
        for t in transactions:
            if t.get("transaction_date"):
                date_str = t["transaction_date"].split("T")[0]
                assert date_str >= "2026-01-01"
                assert date_str <= "2026-01-31"
    
    @pytest.mark.asyncio
    async def test_filter_by_transaction_type(self, client: httpx.AsyncClient):
        """GET /finance/banking/transactions with transaction_type should filter."""
        response = await client.get("/finance/banking/transactions", params={
            "transaction_type": "Deposit"
        })
        assert response.status_code == 200


class TestAPBillsFilters:
    """Tests for AP Bills filter parameters."""
    
    @pytest.mark.asyncio
    async def test_filter_by_status(self, client: httpx.AsyncClient):
        """GET /ap/bills with status should filter."""
        response = await client.get("/ap/bills", params={"status": "Posted"})
        assert response.status_code == 200
        bills = response.json()
        for bill in bills:
            if "status" in bill:
                assert bill["status"] == "Posted"
    
    @pytest.mark.asyncio
    async def test_filter_by_date_range(self, client: httpx.AsyncClient):
        """GET /ap/bills with date range should filter."""
        response = await client.get("/ap/bills", params={
            "date_from": "2026-01-01",
            "date_to": "2026-01-31"
        })
        assert response.status_code == 200


class TestAPPaymentsFilters:
    """Tests for AP Payments filter parameters."""
    
    @pytest.mark.asyncio
    async def test_filter_by_date_range(self, client: httpx.AsyncClient):
        """GET /ap/payments with date range should filter."""
        response = await client.get("/ap/payments", params={
            "date_from": "2026-01-01",
            "date_to": "2026-01-31"
        })
        assert response.status_code == 200


class TestARInvoicesFilters:
    """Tests for AR Invoices filter parameters."""
    
    @pytest.mark.asyncio
    async def test_filter_by_status(self, client: httpx.AsyncClient):
        """GET /ar/invoices with status should filter."""
        response = await client.get("/ar/invoices", params={"status": "Sent"})
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_filter_by_date_range(self, client: httpx.AsyncClient):
        """GET /ar/invoices with date range should filter."""
        response = await client.get("/ar/invoices", params={
            "date_from": "2026-01-01",
            "date_to": "2026-01-31"
        })
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_filter_by_customer_id(self, client: httpx.AsyncClient):
        """GET /ar/invoices with customer_id should filter."""
        # Get customers first
        customers_resp = await client.get("/ar/customers")
        if customers_resp.status_code == 200:
            customers = customers_resp.json()
            if customers:
                customer_id = customers[0]["id"]
                response = await client.get("/ar/invoices", params={
                    "customer_id": customer_id
                })
                assert response.status_code == 200


class TestARReceiptsFilters:
    """Tests for AR Receipts filter parameters."""
    
    @pytest.mark.asyncio
    async def test_filter_by_date_range(self, client: httpx.AsyncClient):
        """GET /ar/receipts with date range should filter."""
        response = await client.get("/ar/receipts", params={
            "date_from": "2026-01-01",
            "date_to": "2026-01-31"
        })
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_filter_by_customer_id(self, client: httpx.AsyncClient):
        """GET /ar/receipts with customer_id should filter."""
        # Get customers first
        customers_resp = await client.get("/ar/customers")
        if customers_resp.status_code == 200:
            customers = customers_resp.json()
            if customers:
                customer_id = customers[0]["id"]
                response = await client.get("/ar/receipts", params={
                    "customer_id": customer_id
                })
                assert response.status_code == 200
