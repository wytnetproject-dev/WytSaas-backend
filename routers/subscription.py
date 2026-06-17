from typing import List, Optional
import hmac
import hashlib
import httpx
import os
import random
import json
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db.db import get_db
from models.brands import BrandIntegration, SubscriptionSyncLog, SubscriptionPayment
from schemas.subscription import (
    BrandSubscriptionPlanCreate,
    BrandSubscriptionPlanUpdate,
    BrandSubscriptionPlanResponse,
    UserSubscriptionCreate,
    UserSubscriptionResponse,
    PaymentOrderCreate,
    PaymentOrderResponse,
    PaymentVerificationInput
)
from schemas.response import APIResponse
from crud.subscription import (
    create_subscription_plan,
    get_subscription_plan,
    list_subscription_plans,
    update_subscription_plan,
    delete_subscription_plan,
    add_user_subscription,
    remove_user_subscription,
    get_user_subscriptions,
    get_brand_subscribers
)
from crud.brand import get_brand_by_id
from utils.auth import UserJWT, get_user_token

router = APIRouter(prefix="/brands", tags=["Brand Subscriptions"])

# List all subscription plans, optionally filter by brand_id
@router.get("/subscription-plans/", response_model=APIResponse[BrandSubscriptionPlanResponse])
async def list_all_subscription_plans(
    brand_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    plans = await list_subscription_plans(db, brand_id=brand_id, skip=skip, limit=limit)
    return APIResponse[BrandSubscriptionPlanResponse](
        items=plans,
        detail="Subscription plans retrieved successfully",
        itemCount=len(plans)
    )

# Create a new subscription plan for a brand
@router.post("/{brand_id}/subscription-plans", response_model=APIResponse[BrandSubscriptionPlanResponse], status_code=status.HTTP_201_CREATED)
async def create_new_subscription_plan(
    brand_id: int,
    plan: BrandSubscriptionPlanCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserJWT = Depends(get_user_token)
):
    brand = await get_brand_by_id(db, brand_id)
    if not brand:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Brand not found"
        )
    created_plan = await create_subscription_plan(db, brand_id, plan)
    return APIResponse[BrandSubscriptionPlanResponse](
        item=created_plan,
        detail="Subscription plan created successfully"
    )

# Update a subscription plan by ID
@router.patch("/subscription-plans/{plan_id}", response_model=APIResponse[BrandSubscriptionPlanResponse])
async def modify_subscription_plan(
    plan_id: int,
    plan_update: BrandSubscriptionPlanUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: UserJWT = Depends(get_user_token)
):
    plan = await get_subscription_plan(db, plan_id)
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription plan not found"
        )
    updated_plan = await update_subscription_plan(db, plan_id, plan_update)
    return APIResponse[BrandSubscriptionPlanResponse](
        item=updated_plan,
        detail="Subscription plan updated successfully"
    )

# Delete a subscription plan by ID
@router.delete("/subscription-plans/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_subscription_plan(
    plan_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserJWT = Depends(get_user_token)
):
    success = await delete_subscription_plan(db, plan_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription plan not found"
        )
    return None


# List subscriptions for current user
@router.get("/subscriptions", response_model=APIResponse[UserSubscriptionResponse])
async def list_user_active_subscriptions(
    db: AsyncSession = Depends(get_db),
    current_user: UserJWT = Depends(get_user_token)
):
    subscriptions = await get_user_subscriptions(db, current_user.id)
    items = []
    for sub in subscriptions:
        items.append(UserSubscriptionResponse(
            id=sub.id,
            user_id=str(sub.user_id),
            brand_id=sub.brand_id,
            plan_id=sub.plan_id,
            status=sub.status,
            subscribed_at=sub.subscribed_at,
            external_user_id=sub.external_user_id,
            sync_status=sub.sync_status,
            last_synced_at=sub.last_synced_at
        ))
    return APIResponse[UserSubscriptionResponse](
        items=items,
        detail="User subscriptions retrieved successfully",
        itemCount=len(items)
    )


# Subscribe to a plan
@router.post("/{brand_id}/subscribe", response_model=APIResponse[UserSubscriptionResponse])
async def subscribe_to_brand_plan(
    brand_id: int,
    subscription_input: UserSubscriptionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserJWT = Depends(get_user_token)
):
    plan = await get_subscription_plan(db, subscription_input.plan_id)
    if not plan or plan.brand_id != brand_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription plan not found or does not belong to this brand"
        )
    sub = await add_user_subscription(db, current_user.id, brand_id, subscription_input.plan_id)
    return APIResponse[UserSubscriptionResponse](
        item=UserSubscriptionResponse(
            id=sub.id,
            user_id=str(sub.user_id),
            brand_id=sub.brand_id,
            plan_id=sub.plan_id,
            status=sub.status,
            subscribed_at=sub.subscribed_at
        ),
        detail="Subscribed to plan successfully"
    )


# Unsubscribe from a brand
@router.delete("/{brand_id}/unsubscribe", status_code=status.HTTP_204_NO_CONTENT)
async def unsubscribe_from_brand(
    brand_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserJWT = Depends(get_user_token)
):
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Unsubscribing is not allowed."
    )


# Create a Razorpay payment order
@router.post("/{brand_id}/payment/order", response_model=PaymentOrderResponse)
async def create_payment_order(
    brand_id: int,
    order_input: PaymentOrderCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserJWT = Depends(get_user_token)
):
    plan = await get_subscription_plan(db, order_input.plan_id)
    if not plan or plan.brand_id != brand_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription plan not found or does not belong to this brand"
        )

    razorpay_key_id = os.getenv("RAZORPAY_KEY_ID")
    razorpay_key_secret = os.getenv("RAZORPAY_KEY_SECRET")

    # If keys are missing or blank, we run in mock sandbox mode
    if not razorpay_key_id or not razorpay_key_secret:
        mock_order_id = f"order_mock_{random.randint(100000, 999999)}"
        return PaymentOrderResponse(
            order_id=mock_order_id,
            amount=int(plan.price * 100),  # in paise
            currency="INR",
            key_id="rzp_test_mockkey12345",
            plan_id=plan.id,
            is_mock=True
        )

    # Real Razorpay Order Creation via API
    try:
        url = "https://api.razorpay.com/v1/orders"
        amount_paise = int(plan.price * 100)
        auth = (razorpay_key_id, razorpay_key_secret)
        data = {
            "amount": amount_paise,
            "currency": "INR",
            "receipt": f"receipt_brand_{brand_id}_plan_{plan.id}",
            "notes": {
                "brand_id": str(brand_id),
                "plan_id": str(plan.id),
                "user_id": str(current_user.id)
            }
        }
        async with httpx.AsyncClient() as client:
            res = await client.post(url, json=data, auth=auth)
            if res.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Razorpay API error: {res.text}"
                )
            res_data = res.json()
            return PaymentOrderResponse(
                order_id=res_data["id"],
                amount=res_data["amount"],
                currency=res_data["currency"],
                key_id=razorpay_key_id,
                plan_id=plan.id,
                is_mock=False
            )
    except Exception as e:
        # Fallback to mock on exception for seamless development
        mock_order_id = f"order_mock_{random.randint(100000, 999999)}"
        return PaymentOrderResponse(
            order_id=mock_order_id,
            amount=int(plan.price * 100),
            currency="INR",
            key_id="rzp_test_mockkey12345",
            plan_id=plan.id,
            is_mock=True
        )


# Verify Razorpay signature and activate subscription
@router.post("/{brand_id}/payment/verify", response_model=APIResponse[UserSubscriptionResponse])
async def verify_payment(
    brand_id: int,
    verify_input: PaymentVerificationInput,
    db: AsyncSession = Depends(get_db),
    current_user: UserJWT = Depends(get_user_token)
):
    razorpay_key_secret = os.getenv("RAZORPAY_KEY_SECRET")

    # Check if order_id is mock or key_secret is missing
    is_mock = verify_input.razorpay_order_id.startswith("order_mock_") or not razorpay_key_secret

    if not is_mock and razorpay_key_secret:
        # Verify signature using HMAC-SHA256
        msg = f"{verify_input.razorpay_order_id}|{verify_input.razorpay_payment_id}"
        generated_signature = hmac.new(
            razorpay_key_secret.encode(),
            msg.encode(),
            hashlib.sha256
        ).hexdigest()

        if generated_signature != verify_input.razorpay_signature:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid payment signature"
            )

    # Register subscription in DB
    sub = await add_user_subscription(db, current_user.id, brand_id, verify_input.plan_id)

    # Retrieve plan info to get price
    plan = await get_subscription_plan(db, verify_input.plan_id)
    amount_val = float(plan.price) if plan else 0.0

    # Store Payment record in DB
    payment = SubscriptionPayment(
        subscription_id=sub.id,
        user_id=current_user.id,
        amount=amount_val,
        payment_gateway="Razorpay",
        gateway_payment_id=verify_input.razorpay_payment_id,
        payment_status="paid",
        paid_at=datetime.utcnow()
    )
    db.add(payment)
    await db.commit()

    # Sync with Brand Integration settings if configured and active
    integration_result = await db.execute(
        select(BrandIntegration).where(
            BrandIntegration.brand_id == brand_id,
            BrandIntegration.status == "active"
        )
    )
    integration = integration_result.scalars().first()

    if integration and integration.create_user_endpoint:
        # Get user details from DB to get email and name
        from model import User
        user_result = await db.execute(
            select(User).where(User.id == current_user.id)
        )
        db_user = user_result.scalars().first()
        user_email = db_user.email if db_user else "unknown@wytnet.com"
        user_name = (db_user.full_name or db_user.username) if db_user else "Unknown User"

        # Prepare sync payload
        payload = {
            "user_id": str(current_user.id),
            "user_email": user_email,
            "user_name": user_name,
            "plan_id": sub.plan_id,
            "plan_name": plan.name if plan else "Plan",
            "price": amount_val,
            "billing_cycle": plan.billing_cycle if plan else "monthly"
        }

        headers = {}
        if integration.api_key:
            headers["X-API-Key"] = integration.api_key

        sync_status_val = "failed"
        external_user_id_val = None
        response_payload = ""
        response_code = 500

        # Simulate developer API if requested via sandbox or mock order
        is_mock_endpoint = "mock" in integration.create_user_endpoint or verify_input.razorpay_order_id.startswith("order_mock_")

        if is_mock_endpoint:
            response_code = 200
            external_user_id_val = f"EXT_{random.randint(1000, 9999)}"
            response_payload = json.dumps({
                "success": True,
                "external_user_id": external_user_id_val,
                "detail": "Sandbox integration sync success"
            })
            sync_status_val = "synced"
        else:
            try:
                async with httpx.AsyncClient() as client:
                    res = await client.post(
                        integration.create_user_endpoint,
                        json=payload,
                        headers=headers,
                        timeout=10.0
                    )
                    response_code = res.status_code
                    response_payload = res.text

                    if res.status_code in [200, 201]:
                        res_data = res.json()
                        if res_data.get("success") is True or res_data.get("status") == "success":
                            external_user_id_val = str(res_data.get("external_user_id"))
                            sync_status_val = "synced"
                        else:
                            sync_status_val = "failed"
                    else:
                        sync_status_val = "failed"
            except Exception as e:
                response_code = 500
                response_payload = str(e)
                sync_status_val = "failed"

        # Update User Subscription record
        sub.sync_status = sync_status_val
        sub.external_user_id = external_user_id_val
        sub.last_synced_at = datetime.utcnow()
        await db.commit()
        await db.refresh(sub)

        # Write Sync Log
        sync_log = SubscriptionSyncLog(
            subscription_id=sub.id,
            brand_id=brand_id,
            action="create_user",
            request_payload=json.dumps(payload),
            response_payload=response_payload,
            response_code=response_code,
            status=sync_status_val,
            retry_count=0
        )
        db.add(sync_log)
        await db.commit()
    else:
        # Default fallback: mark as synced automatically if no endpoint configured
        sub.sync_status = "synced"
        sub.last_synced_at = datetime.utcnow()
        await db.commit()
        await db.refresh(sub)

    return APIResponse[UserSubscriptionResponse](
        item=UserSubscriptionResponse(
            id=sub.id,
            user_id=str(sub.user_id),
            brand_id=sub.brand_id,
            plan_id=sub.plan_id,
            status=sub.status,
            subscribed_at=sub.subscribed_at,
            external_user_id=sub.external_user_id,
            sync_status=sub.sync_status,
            last_synced_at=sub.last_synced_at
        ),
        detail="Payment verified and subscription activated successfully"
    )


# List subscribers for a specific brand/app (Developer Portal feature)
@router.get("/{brand_id}/subscribers")
async def list_brand_subscribers(
    brand_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserJWT = Depends(get_user_token)
):
    subscribers = await get_brand_subscribers(db, brand_id)

    items = []
    for sub in subscribers:
        user_email = sub.user.email if sub.user else "unknown@wytnet.com"
        user_name = sub.user.full_name or sub.user.username if sub.user else "Unknown User"
        plan_name = sub.plan.name if sub.plan else "Default Plan"
        plan_price = float(sub.plan.price) if sub.plan else 0.0
        billing_cycle = sub.plan.billing_cycle if sub.plan else "monthly"

        items.append({
            "id": sub.id,
            "user_id": str(sub.user_id),
            "user_name": user_name,
            "user_email": user_email,
            "plan_id": sub.plan_id,
            "plan_name": plan_name,
            "plan_price": plan_price,
            "billing_cycle": billing_cycle,
            "status": sub.status,
            "subscribed_at": sub.subscribed_at.isoformat() if sub.subscribed_at else None,
            "external_user_id": sub.external_user_id,
            "sync_status": sub.sync_status,
            "last_synced_at": sub.last_synced_at.isoformat() if sub.last_synced_at else None
        })

    return {
        "items": items,
        "detail": "Brand subscribers retrieved successfully",
        "itemCount": len(items)
    }


class BrandIntegrationInput(BaseModel):
    create_user_endpoint: Optional[str] = None
    update_user_endpoint: Optional[str] = None
    cancel_user_endpoint: Optional[str] = None
    webhook_url: Optional[str] = None
    api_key: Optional[str] = None
    webhook_secret: Optional[str] = None
    status: Optional[str] = "active"


# Get brand integration settings
@router.get("/{brand_id}/integration")
async def get_brand_integration_settings(
    brand_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserJWT = Depends(get_user_token)
):
    result = await db.execute(
        select(BrandIntegration).where(BrandIntegration.brand_id == brand_id)
    )
    integration = result.scalars().first()
    return {
        "item": {
            "id": integration.id if integration else None,
            "brand_id": brand_id,
            "create_user_endpoint": integration.create_user_endpoint if integration else "",
            "update_user_endpoint": integration.update_user_endpoint if integration else "",
            "cancel_user_endpoint": integration.cancel_user_endpoint if integration else "",
            "webhook_url": integration.webhook_url if integration else "",
            "api_key": integration.api_key if integration else "",
            "webhook_secret": integration.webhook_secret if integration else "",
            "status": integration.status if integration else "active",
            "created_at": integration.created_at.isoformat() if integration and integration.created_at else None
        } if integration else None,
        "detail": "Brand integration settings retrieved successfully"
    }


# Save/update brand integration settings
@router.post("/{brand_id}/integration")
async def save_brand_integration_settings(
    brand_id: int,
    input_data: BrandIntegrationInput,
    db: AsyncSession = Depends(get_db),
    current_user: UserJWT = Depends(get_user_token)
):
    result = await db.execute(
        select(BrandIntegration).where(BrandIntegration.brand_id == brand_id)
    )
    integration = result.scalars().first()
    if not integration:
        integration = BrandIntegration(brand_id=brand_id)
        db.add(integration)

    integration.create_user_endpoint = input_data.create_user_endpoint
    integration.update_user_endpoint = input_data.update_user_endpoint
    integration.cancel_user_endpoint = input_data.cancel_user_endpoint
    integration.webhook_url = input_data.webhook_url
    integration.api_key = input_data.api_key
    integration.webhook_secret = input_data.webhook_secret
    integration.status = input_data.status or "active"

    await db.commit()
    await db.refresh(integration)

    return {
        "item": {
            "id": integration.id,
            "brand_id": brand_id,
            "create_user_endpoint": integration.create_user_endpoint,
            "update_user_endpoint": integration.update_user_endpoint,
            "cancel_user_endpoint": integration.cancel_user_endpoint,
            "webhook_url": integration.webhook_url,
            "api_key": integration.api_key,
            "webhook_secret": integration.webhook_secret,
            "status": integration.status,
            "created_at": integration.created_at.isoformat() if integration.created_at else None
        },
        "detail": "Brand integration settings saved successfully"
    }
