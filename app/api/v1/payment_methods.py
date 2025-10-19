from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.payment_method import (
    PaymentMethodCreate,
    PaymentMethodUpdate,
    PaymentMethodResponse,
    PaymentMethodListResponse
)
from app.crud import payment_method as payment_method_crud

router = APIRouter(prefix="/payment-methods", tags=["Payment Methods"])


@router.get("", response_model=PaymentMethodListResponse)
async def get_payment_methods(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all payment methods for the current user.
    
    Returns a list of payment methods sorted by:
    - Default payment method first
    - Then by creation date (newest first)
    """
    payment_methods = await payment_method_crud.get_payment_methods(db, current_user.id)
    
    return PaymentMethodListResponse(
        payment_methods=payment_methods,
        total=len(payment_methods)
    )


@router.post("", response_model=PaymentMethodResponse, status_code=status.HTTP_201_CREATED)
async def create_payment_method(
    payment_method: PaymentMethodCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new payment method for the current user.
    
    **Bank Account Details:**
    - bank_name: Name of the bank (2-100 characters)
    - account_number: Bank account number (9-18 digits)
    - ifsc_code: IFSC code (11 characters, format: XXXX0XXXXXX)
    - account_holder_name: Name of account holder (2-100 characters)
    
    **UPI Details:**
    - upi_name: UPI provider name (2-100 characters, e.g., "PayTM", "Google Pay")
    - upi_id: UPI ID (format: username@provider, e.g., "john@paytm")
    
    **Note:** The first payment method added is automatically set as default.
    """
    try:
        db_payment_method = await payment_method_crud.create_payment_method(
            db, current_user.id, payment_method
        )
        return db_payment_method
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{payment_method_id}", response_model=PaymentMethodResponse)
async def get_payment_method(
    payment_method_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific payment method by ID.
    
    Only the owner can access their payment methods.
    """
    db_payment_method = await payment_method_crud.get_payment_method_by_id(
        db, payment_method_id, current_user.id
    )
    
    if not db_payment_method:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment method not found"
        )
    
    return db_payment_method


@router.put("/{payment_method_id}", response_model=PaymentMethodResponse)
async def update_payment_method(
    payment_method_id: int,
    payment_method_update: PaymentMethodUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update a payment method.
    
    You can update:
    - name: Display name
    - details: Bank or UPI details
    
    **Note:** You cannot change the payment method type (bank/UPI).
    """
    db_payment_method = await payment_method_crud.update_payment_method(
        db, payment_method_id, current_user.id, payment_method_update
    )
    
    if not db_payment_method:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment method not found"
        )
    
    return db_payment_method


@router.delete("/{payment_method_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_payment_method(
    payment_method_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a payment method.
    
    **Rules:**
    - Cannot delete the only payment method (must have at least one)
    - If deleting the default payment method, another one will be automatically set as default
    """
    success = await payment_method_crud.delete_payment_method(
        db, payment_method_id, current_user.id
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment method not found"
        )
    
    return None


@router.patch("/{payment_method_id}/set-default", response_model=PaymentMethodResponse)
async def set_default_payment_method(
    payment_method_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Set a payment method as the default.
    
    This will remove the default flag from all other payment methods.
    """
    db_payment_method = await payment_method_crud.set_default_payment_method(
        db, payment_method_id, current_user.id
    )
    
    if not db_payment_method:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment method not found"
        )
    
    return db_payment_method
