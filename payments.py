"""Stripe Payments — subscriptions + marketplace purchases"""
from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from jose import jwt, JWTError
import stripe, os

router = APIRouter()
security = HTTPBearer()
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

PLANS = {
    "starter": {"price_id": os.getenv("STRIPE_PRICE_STARTER"), "credits": 50,  "name": "Starter"},
    "pro":     {"price_id": os.getenv("STRIPE_PRICE_PRO"),     "credits": 500, "name": "Pro"},
    "agency":  {"price_id": os.getenv("STRIPE_PRICE_AGENCY"),  "credits": -1,  "name": "Agency"},
}

def get_user(creds: HTTPAuthorizationCredentials = Depends(security)):
    try:
        return jwt.decode(creds.credentials, os.getenv("SECRET_KEY","change-me"), algorithms=["HS256"])
    except JWTError:
        raise HTTPException(401, "Invalid token")

class CheckoutIn(BaseModel):
    plan: str  # starter | pro | agency

class MarketplacePurchaseIn(BaseModel):
    product_id: str
    price_cents: int

@router.post("/checkout")
async def create_checkout(body: CheckoutIn, user: dict = Depends(get_user)):
    """Create Stripe checkout session for subscription"""
    plan = PLANS.get(body.plan)
    if not plan:
        raise HTTPException(400, "Invalid plan")
    session = stripe.checkout.Session.create(
        mode="subscription",
        line_items=[{"price": plan["price_id"], "quantity": 1}],
        success_url=f"{os.getenv('FRONTEND_URL')}/dashboard.html?upgrade=success",
        cancel_url=f"{os.getenv('FRONTEND_URL')}/pricing.html",
        metadata={"user_id": user["sub"], "plan": body.plan},
        customer_email=user.get("email"),
    )
    return {"checkout_url": session.url, "session_id": session.id}

@router.post("/marketplace/buy")
async def buy_marketplace_product(body: MarketplacePurchaseIn, user: dict = Depends(get_user)):
    """One-time purchase for marketplace product"""
    session = stripe.checkout.Session.create(
        mode="payment",
        line_items=[{"price_data": {
            "currency": "usd",
            "unit_amount": body.price_cents,
            "product_data": {"name": f"ProductAI Digital Product #{body.product_id}"}
        }, "quantity": 1}],
        success_url=f"{os.getenv('FRONTEND_URL')}/marketplace.html?purchase=success&product={body.product_id}",
        cancel_url=f"{os.getenv('FRONTEND_URL')}/marketplace.html",
        metadata={"user_id": user["sub"], "product_id": body.product_id, "type": "marketplace"},
    )
    return {"checkout_url": session.url}

@router.post("/webhook")
async def stripe_webhook(request: Request):
    """Handle Stripe webhook events"""
    payload = await request.body()
    sig = request.headers.get("stripe-signature")
    try:
        event = stripe.Webhook.construct_event(payload, sig, os.getenv("STRIPE_WEBHOOK_SECRET"))
    except Exception:
        raise HTTPException(400, "Invalid webhook signature")

    from supabase import create_client
    sb = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_KEY"))

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        meta = session.get("metadata", {})
        user_id = meta.get("user_id")
        plan = meta.get("plan")

        if plan and user_id:
            plan_data = PLANS.get(plan, {})
            sb.table("users").update({
                "plan": plan,
                "credits": plan_data.get("credits", 50),
                "stripe_customer_id": session.get("customer")
            }).eq("id", user_id).execute()

        elif meta.get("type") == "marketplace":
            product_id = meta.get("product_id")
            sb.table("purchases").insert({
                "user_id": user_id,
                "product_id": product_id,
                "amount_cents": session.get("amount_total", 0),
            }).execute()

    elif event["type"] == "customer.subscription.deleted":
        customer_id = event["data"]["object"]["customer"]
        sb.table("users").update({"plan": "free", "credits": 3}).eq("stripe_customer_id", customer_id).execute()

    return {"received": True}

@router.get("/portal")
async def billing_portal(user: dict = Depends(get_user)):
    """Stripe customer portal for managing subscription"""
    from supabase import create_client
    sb = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_KEY"))
    result = sb.table("users").select("stripe_customer_id").eq("id", user["sub"]).execute()
    if not result.data or not result.data[0].get("stripe_customer_id"):
        raise HTTPException(400, "No billing account found")
    session = stripe.billing_portal.Session.create(
        customer=result.data[0]["stripe_customer_id"],
        return_url=f"{os.getenv('FRONTEND_URL')}/dashboard.html",
    )
    return {"portal_url": session.url}
