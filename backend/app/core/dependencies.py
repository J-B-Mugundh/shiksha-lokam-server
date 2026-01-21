from fastapi import Depends, HTTPException

'''
async def get_current_user():
    # Replace later with JWT logic
    return {
        "_id": "mock_user_id",
        "displayName": "Test User"
    }
'''
async def get_current_user():
    return {
        "_id": "test-user-id",
        "email": "test@example.com",
        "displayName": "Test User",
        "platformRole": "admin",
    }
