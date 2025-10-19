from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List

from app.models.user_file import UserFile, FileType


async def create_user_file(
    db: AsyncSession, 
    user_id: int, 
    file_type: FileType, 
    filename: str, 
    file_path: str
) -> UserFile:
    """Create a new user file record"""
    db_file = UserFile(
        user_id=user_id,
        file_type=file_type,
        filename=filename,
        file_path=file_path
    )
    db.add(db_file)
    await db.commit()
    await db.refresh(db_file)
    return db_file


async def get_user_file_by_type(
    db: AsyncSession, 
    user_id: int, 
    file_type: FileType
) -> Optional[UserFile]:
    """Get user file by type (latest one)"""
    result = await db.execute(
        select(UserFile)
        .where(UserFile.user_id == user_id, UserFile.file_type == file_type)
        .order_by(UserFile.uploaded_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def get_user_files(db: AsyncSession, user_id: int) -> List[UserFile]:
    """Get all files for a user"""
    result = await db.execute(
        select(UserFile)
        .where(UserFile.user_id == user_id)
        .order_by(UserFile.uploaded_at.desc())
    )
    return result.scalars().all()


async def delete_user_file(db: AsyncSession, file_id: int, user_id: int) -> bool:
    """Delete a user file"""
    result = await db.execute(
        select(UserFile).where(UserFile.id == file_id, UserFile.user_id == user_id)
    )
    db_file = result.scalar_one_or_none()
    
    if not db_file:
        return False
    
    await db.delete(db_file)
    await db.commit()
    return True


async def check_user_has_required_files(db: AsyncSession, user_id: int) -> dict:
    """Check if user has uploaded both document and selfie"""
    document = await get_user_file_by_type(db, user_id, FileType.KYC_DOCUMENT)
    selfie = await get_user_file_by_type(db, user_id, FileType.KYC_SELFIE)
    
    return {
        "has_document": document is not None,
        "has_selfie": selfie is not None,
        "document_path": document.file_path if document else None,
        "selfie_path": selfie.file_path if selfie else None,
        "ready_for_submission": document is not None and selfie is not None
    }
