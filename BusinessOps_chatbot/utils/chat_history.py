import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from pymongo import MongoClient
from pymongo.errors import ConnectionError

# --- MongoDB Connection Setup ---
def get_mongo_db():
    """
    Dependency to provide MongoDB connection.
    Returns the chat database instance.
    """
    try:
        # Replace with your MongoDB connection string
        # Example: "mongodb://username:password@localhost:27017/"
        client = MongoClient("mongodb://localhost:27017/")
        
        # Test the connection
        client.admin.command('ping')
        
        # Return the database instance (replace 'hr_chat_db' with your preferred DB name)
        return client["hr_chat_db"]
    except ConnectionError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to connect to MongoDB: {str(e)}"
        )

router = APIRouter(prefix="/chat_history", tags=["Chat History"])

# --- PLACEHOLDER: Uncomment and use your actual authentication function ---
# from dependencies.auth_ import verify_token

# ------------------ Pydantic Models ------------------ #

class ChatItem(BaseModel):
    chat_id: str
    title: str
    created_at: datetime.datetime
    last_updated: datetime.datetime
    bookmarked: bool = False

class MessageItem(BaseModel):
    timestamp: datetime.datetime
    sender: str
    message: str

class ChatDetail(BaseModel):
    chat_id: str
    title: str
    messages: List[MessageItem]
    created_at: datetime.datetime
    last_updated: Optional[datetime.datetime] = None
    bookmarked: bool = False

# ------------------ Utility Function ------------------ #
def _get_paginated_chats(collection, user_id: str, tenant_id: Optional[str], page: int, limit: int):
    query = {"user_id": user_id}
    if tenant_id:
        query["tenant_id"] = tenant_id

    total_items = collection.count_documents(query)
    total_pages = (total_items // limit) + (1 if total_items % limit else 0)

    cursor = (
        collection.find(query)
        .sort("last_updated", -1)
        .skip((page - 1) * limit)
        .limit(limit)
    )
    results = list(cursor)
    return results, total_items, total_pages

# ------------------ Routes ------------------ #

@router.get("/get_chats")
async def get_chats(
    db = Depends(get_mongo_db),
    # token: str = Depends(verify_token),
    tenant_id: Optional[str] = Query(None, description="Tenant ID for multi-tenancy"),
    page: int = Query(1, ge=1, description="Page number for pagination"),
    limit: int = Query(10, ge=1, le=100, description="Number of results per page"),
):
    try:
        user_id = "demo_user@company.com"  # PLACEHOLDER for user extraction from token
        collection = db["chat_sessions"]
        
        results, total_items, total_pages = _get_paginated_chats(
            collection, user_id, tenant_id, page, limit
        )

        if not results:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No chat sessions found."
            )

        response_data = []
        for doc in results:
            chat_item = ChatItem(
                chat_id=str(doc.get("chat_id")),
                title=doc.get("title", ""),
                created_at=doc.get("created_at", datetime.datetime.utcnow()),
                last_updated=doc.get("last_updated", datetime.datetime.utcnow()),
                bookmarked=doc.get("bookmarked", False)
            )
            response_data.append(chat_item.dict())

        return {
            "status": "success",
            "data": response_data,
            "pagination": {
                "current_page": page,
                "total_pages": total_pages,
                "total_items": total_items
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Server issue while fetching chats: {e}"
        )

@router.get("/get_specific_chat/{chat_id}")
async def get_specific_chat(
    chat_id: str,
    db = Depends(get_mongo_db),
    # token: str = Depends(verify_token)
):
    try:
        user_id = "demo_user@company.com"
        collection = db["chat_sessions"]
        doc = collection.find_one({"chat_id": chat_id, "user_id": user_id})

        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat with the provided ID does not exist."
            )

        chat_detail = ChatDetail(
            chat_id=str(doc["chat_id"]),
            title=doc.get("title", ""),
            messages=[
                MessageItem(
                    timestamp=m.get("timestamp", datetime.datetime.utcnow()),
                    sender=m.get("sender", ""),
                    message=m.get("message", "")
                )
                for m in doc.get("messages", [])
            ],
            created_at=doc.get("created_at", datetime.datetime.utcnow()),
            last_updated=doc.get("last_updated", datetime.datetime.utcnow()),
            bookmarked=doc.get("bookmarked", False),
        )

        return {
            "status": "success",
            "data": chat_detail.dict()
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving specific chat: {e}"
        )

@router.put("/rename_chat/{chat_id}")
async def rename_chat(
    chat_id: str,
    payload: dict,
    db = Depends(get_mongo_db),
    # token: str = Depends(verify_token)
):
    try:
        user_id = "demo_user@company.com"
        new_title = payload.get("new_title", "")

        if not new_title or not isinstance(new_title, str):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid title format. The title must be a non-empty string."
            )

        collection = db["chat_sessions"]
        result = collection.update_one(
            {"chat_id": chat_id, "user_id": user_id},
            {
                "$set": {
                    "title": new_title,
                    "last_updated": datetime.datetime.utcnow()
                }
            }
        )
        if result.matched_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat with the provided ID does not exist."
            )

        return {
            "status": "success",
            "message": "Chat renamed successfully."
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Server issue while renaming chat: {e}"
        )

@router.delete("/delete_chat/{chat_id}")
async def delete_chat(
    chat_id: str,
    db = Depends(get_mongo_db),
    # token: str = Depends(verify_token)
):
    try:
        user_id = "demo_user@company.com"
        collection = db["chat_sessions"]
        result = collection.delete_one({"chat_id": chat_id, "user_id": user_id})

        if result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat with the provided ID does not exist."
            )

        return {
            "status": "success",
            "message": "Chat deleted successfully."
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred while deleting the chat: {e}"
        )

@router.post("/bookmark_chat/{chat_id}")
async def bookmark_chat(
    chat_id: str,
    db = Depends(get_mongo_db),
    # token: str = Depends(verify_token)
):
    try:
        user_id = "demo_user@company.com"
        collection = db["chat_sessions"]
        doc = collection.find_one({"chat_id": chat_id, "user_id": user_id})
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat with the provided ID does not exist."
            )
        new_bookmark_state = not doc.get("bookmarked", False)
        collection.update_one(
            {"chat_id": chat_id, "user_id": user_id},
            {"$set": {"bookmarked": new_bookmark_state, "last_updated": datetime.datetime.utcnow()}}
        )

        return {
            "status": "success",
            "message": "Chat bookmarked successfully."
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error bookmarking chat: {e}"
        )
