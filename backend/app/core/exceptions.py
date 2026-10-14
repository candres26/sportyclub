from fastapi import status


class AppError(Exception):
    status_code: int = status.HTTP_400_BAD_REQUEST
    detail: str = "Error de la aplicacion"

    def __init__(self, detail: str | None = None) -> None:
        if detail is not None:
            self.detail = detail
        super().__init__(self.detail)


class BadRequestError(AppError):
    status_code = status.HTTP_400_BAD_REQUEST


class UnauthorizedError(AppError):
    status_code = status.HTTP_401_UNAUTHORIZED
    detail = "No autenticado"


class ForbiddenError(AppError):
    status_code = status.HTTP_403_FORBIDDEN
    detail = "No autorizado"


class NotFoundError(AppError):
    status_code = status.HTTP_404_NOT_FOUND
    detail = "Recurso no encontrado"


class ConflictError(AppError):
    status_code = status.HTTP_409_CONFLICT
    detail = "Conflicto con un recurso existente"


class TenantNotFoundError(NotFoundError):
    detail = "Club no encontrado"
