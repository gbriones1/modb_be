from fastapi import HTTPException, status


LoginException = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


PermException = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="User unauthorized",
        headers={"WWW-Authenticate": "Bearer"},
    )

UserNotFoundException = HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="User not found"
    )