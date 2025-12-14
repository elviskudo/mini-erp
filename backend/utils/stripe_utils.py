import os
import stripe
from models.models_saas import SubscriptionTier

# Dummy Key for Dev
stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "sk_test_dummy")

PRICING_MAP = {
    SubscriptionTier.MAKER: "price_maker_id",
    SubscriptionTier.GROWTH: "price_growth_id",
    SubscriptionTier.ENTERPRISE: "price_enterprise_id"
}

def create_checkout_session(tier: SubscriptionTier, tenant_id: str, success_url: str, cancel_url: str):
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price': PRICING_MAP.get(tier),
                'quantity': 1,
            }],
            mode='subscription',
            success_url=success_url,
            cancel_url=cancel_url,
            client_reference_id=tenant_id,
            metadata={
                "tenant_id": tenant_id,
                "tier": tier
            }
        )
        return session.url
    except Exception as e:
        # Mock for Dev if no key
        if "Invalid API Key" in str(e) or "No API key" in str(e):
            return f"{success_url}?mock_success=true"
        raise e
