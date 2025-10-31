

@router.get("/profile")
async def profile(request: Request, db: AsyncSession = Depends(get_db)):
    # user_id = get_current_user(request)
    # if not user_id:
    #     raise HTTPException(status_code=401, detail="Not authenticated")
    result = await db.execute(select(User).where(User.id == 1))
    user = result.scalars().first()
    res = {
        "name": "aboba",
        "friendCount": 100,
        "photoCount": 20,
        "subscriberCount": 6,
        "posts": [
            {
                "id": 2,
                "user": "aboba",
                "postTime": "2025-10-13T09:45:00.000Z",
                "text": "scam",
                "image": "/images/2.png",
                "likes": 8,
                "comments": ['Отстой']
            }
        ]
    }
    return res
