def extract_subdomain(host: str, base_domain: str) -> str | None:
    """Devuelve el slug del club a partir del Host de la peticion.

    club1.lvh.me        -> club1
    club1.sportyclub.app -> club1
    lvh.me / www.lvh.me / localhost / 127.0.0.1 -> None
    """
    if not host:
        return None

    hostname = host.split(":", 1)[0].strip().lower()
    base = base_domain.strip().lower()

    if not hostname or hostname == base or hostname == f"www.{base}":
        return None

    suffix = f".{base}"
    if hostname.endswith(suffix):
        sub = hostname[: -len(suffix)]
        if sub:
            return sub.split(".")[0]
    return None
