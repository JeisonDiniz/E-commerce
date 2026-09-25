"""
Middleware de headers de segurança HTTP.

Isoladamente nenhum header aqui "impede hackers", mas juntos fecham classes
inteiras de ataque no navegador do cliente (clickjacking, MIME sniffing,
vazamento de referrer, uso indevido de câmera/geolocalização por um iframe
malicioso embutindo a loja). `Strict-Transport-Security` só é enviado quando
a requisição já chegou em HTTPS, para não quebrar o desenvolvimento local
em HTTP simples.
"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
        return response
