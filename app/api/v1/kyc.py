from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import os
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.user import User
from app.models.kyc import KYCRequest, KYCStatus
from app.models.user_file import FileType
from app.schemas.kyc import KYCCreate, KYCResponse, KYCStatusResponse
from app.crud import kyc as kyc_crud, user_file as user_file_crud
from app.core.config import settings

router = APIRouter()


@router.post("/submit", response_model=KYCResponse)
async def submit_kyc(
    kyc_data: KYCCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Submit KYC for verification - requires both document and selfie to be uploaded"""
    
    # Check if user already has a KYC request
    existing_kyc = await kyc_crud.get_kyc_by_user_id(db, current_user.id)
    if existing_kyc:
        if existing_kyc.status == KYCStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="KYC request already submitted and pending review"
            )
        elif existing_kyc.status == KYCStatus.APPROVED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="KYC already approved"
            )
    
    # Check if user has uploaded required files
    file_status = await user_file_crud.check_user_has_required_files(db, current_user.id)
    
    if not file_status["ready_for_submission"]:
        missing_files = []
        if not file_status["has_document"]:
            missing_files.append("identity document")
        if not file_status["has_selfie"]:
            missing_files.append("selfie photo")
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot submit KYC - missing required files: {', '.join(missing_files)}. Please upload all required documents first."
        )
    
    # Create new KYC request with file paths
    kyc_request = await kyc_crud.create_kyc_request_with_files(
        db=db, 
        kyc_data=kyc_data, 
        user_id=current_user.id,
        document_file_path=file_status["document_path"],
        selfie_file_path=file_status["selfie_path"]
    )
    
    return kyc_request


@router.get("/files-status")
async def get_files_status(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user's KYC file upload status"""
    file_status = await user_file_crud.check_user_has_required_files(db, current_user.id)
    
    return {
        "user_id": current_user.id,
        "document_uploaded": file_status["has_document"],
        "selfie_uploaded": file_status["has_selfie"],
        "ready_for_submission": file_status["ready_for_submission"],
        "document_path": file_status["document_path"],
        "selfie_path": file_status["selfie_path"]
    }


@router.get("/status", response_model=KYCStatusResponse)
async def get_kyc_status(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get KYC status"""
    kyc_request = await kyc_crud.get_kyc_by_user_id(db, current_user.id)
    if not kyc_request:
        return KYCStatusResponse(
            status=KYCStatus.PENDING,
            message="KYC not submitted yet"
        )
    
    return KYCStatusResponse(
        status=kyc_request.status,
        message=f"KYC status: {kyc_request.status.value}",
        submitted_at=kyc_request.created_at,
        reviewed_at=kyc_request.reviewed_at,
        rejection_reason=kyc_request.rejection_reason
    )


@router.post("/upload-document")
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Upload KYC document and link to user"""
    # Validate file type
    allowed_extensions = settings.allowed_file_extensions_list
    file_extension = os.path.splitext(file.filename)[1].lower()
    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Allowed types: {', '.join(allowed_extensions)}"
        )
    
    # Check if user already has pending/approved KYC
    existing_kyc = await kyc_crud.get_kyc_by_user_id(db, current_user.id)
    if existing_kyc and existing_kyc.status in [KYCStatus.APPROVED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot upload document - KYC already approved"
        )
    
    # Create upload directory if it doesn't exist
    os.makedirs(settings.UPLOAD_DIRECTORY, exist_ok=True)
    
    # Generate unique filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"kyc_doc_{current_user.id}_{timestamp}{file_extension}"
    file_path = os.path.join(settings.UPLOAD_DIRECTORY, filename)
    
    # Save file
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
    
    # Save file record to database
    user_file = await user_file_crud.create_user_file(
        db=db,
        user_id=current_user.id,
        file_type=FileType.KYC_DOCUMENT,
        filename=filename,
        file_path=file_path
    )
    
    return {
        "message": "Document uploaded successfully",
        "filename": filename,
        "file_path": file_path,
        "file_id": user_file.id,
        "uploaded_at": user_file.uploaded_at
    }


@router.post("/upload-selfie")
async def upload_selfie(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Upload KYC selfie and link to user"""
    # Validate file type (images only)
    allowed_extensions = [".jpg", ".jpeg", ".png"]
    file_extension = os.path.splitext(file.filename)[1].lower()
    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Allowed types: {', '.join(allowed_extensions)}"
        )
    
    # Check if user already has pending/approved KYC
    existing_kyc = await kyc_crud.get_kyc_by_user_id(db, current_user.id)
    if existing_kyc and existing_kyc.status in [KYCStatus.APPROVED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot upload selfie - KYC already approved"
        )
    
    # Create upload directory if it doesn't exist
    os.makedirs(settings.UPLOAD_DIRECTORY, exist_ok=True)
    
    # Generate unique filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"kyc_selfie_{current_user.id}_{timestamp}{file_extension}"
    file_path = os.path.join(settings.UPLOAD_DIRECTORY, filename)
    
    # Save file
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
    
    # Save file record to database
    user_file = await user_file_crud.create_user_file(
        db=db,
        user_id=current_user.id,
        file_type=FileType.KYC_SELFIE,
        filename=filename,
        file_path=file_path
    )
    
    return {
        "message": "Selfie uploaded successfully",
        "filename": filename,
        "file_path": file_path,
        "file_id": user_file.id,
        "uploaded_at": user_file.uploaded_at
    }


@router.get("/verified-data", response_model=dict)
async def get_verified_kyc_data(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get KYC verified data for current user including selfie image
    
    Returns:
    - User KYC information
    - Document details
    - Selfie image path/URL
    - Verification status and dates
    """
    
    # Check if user is KYC verified
    if not current_user.kyc_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not KYC verified"
        )
    
    # Get approved KYC request
    from sqlalchemy import select
    result = await db.execute(
        select(KYCRequest)
        .where(
            KYCRequest.user_id == current_user.id,
            KYCRequest.status == KYCStatus.APPROVED
        )
        .order_by(KYCRequest.reviewed_at.desc())
    )
    kyc_request = result.scalars().first()
    
    if not kyc_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No approved KYC request found"
        )
    
    # Get selfie image
    selfie = await user_file_crud.get_user_file_by_type(
        db, 
        current_user.id, 
        FileType.KYC_SELFIE
    )
    
    # Get document image
    document = await user_file_crud.get_user_file_by_type(
        db, 
        current_user.id, 
        FileType.KYC_DOCUMENT
    )
    
    return {
        "user_id": current_user.id,
        "full_name": kyc_request.full_name,  # Use full_name from KYC request
        "email": current_user.email,
        "phone": current_user.phone,
        "kyc_verified": current_user.kyc_verified,
        "kyc_details": {
            "id": kyc_request.id,
            "status": kyc_request.status.value,
            # Personal Information
            "full_name": kyc_request.full_name,
            "date_of_birth": kyc_request.date_of_birth,
            "nationality": kyc_request.nationality,
            # Address Information
            "address_line_1": kyc_request.address_line_1,
            "address_line_2": kyc_request.address_line_2,
            "city": kyc_request.city,
            "state": kyc_request.state,
            "postal_code": kyc_request.postal_code,
            "country": kyc_request.country,
            # Document Information
            "document_type": kyc_request.document_type.value,
            "document_number": kyc_request.document_number,
            # Timestamps
            "submitted_at": kyc_request.created_at,
            "reviewed_at": kyc_request.reviewed_at
        },
        "files": {
            "selfie": {
                "file_id": selfie.id if selfie else None,
                "filename": selfie.filename if selfie else None,
                "file_path": selfie.file_path if selfie else None,
                "uploaded_at": selfie.uploaded_at if selfie else None,
                "url": f"/uploads/{selfie.filename}" if selfie else None
            } if selfie else None,
            "document": {
                "file_id": document.id if document else None,
                "filename": document.filename if document else None,
                "file_path": document.file_path if document else None,
                "uploaded_at": document.uploaded_at if document else None,
                "url": f"/uploads/{document.filename}" if document else None
            } if document else None
        }
    }
