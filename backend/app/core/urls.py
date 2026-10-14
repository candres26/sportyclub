from app.core.config import settings


def panel_url(slug: str, path: str = "/") -> str:
    """Construye una URL del panel para el subdominio de un club."""
    host = f"{slug}.{settings.base_domain}"
    port = f":{settings.panel_port}" if settings.panel_port else ""
    if not path.startswith("/"):
        path = f"/{path}"
    return f"{settings.panel_scheme}://{host}{port}{path}"
