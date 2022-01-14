from fastapi import HTTPException, status

class ObjectNotFound(HTTPException):

    def __init__(self, name: str, filters: dict) -> None:
        detail = f"{name} with {filters} not found"
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)