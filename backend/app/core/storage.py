"""
Abstração de armazenamento de arquivos (imagens de produto).

O projeto usa disco local hoje (`LocalStorageBackend`), mas o site deve ser
hospedado em algum provedor no futuro — por isso nenhum código de endpoint
ou model conhece "arquivo em disco": todos falam apenas com `StorageBackend`
(save/delete/url_for) e guardam no banco só a `storage_key` (uma chave
relativa, nunca o caminho absoluto nem a URL). Trocar para um backend de
nuvem (S3, Cloudinary etc.) no deploy é implementar uma nova classe aqui e
apontar `STORAGE_BACKEND` para ela — nada mais no projeto muda.
"""
from __future__ import annotations

import abc
from pathlib import Path

from app.core.config import settings


class StorageBackend(abc.ABC):
    @abc.abstractmethod
    def save(self, data: bytes, key: str) -> None: ...

    @abc.abstractmethod
    def delete(self, key: str) -> None: ...

    @abc.abstractmethod
    def url_for(self, key: str) -> str: ...


class LocalStorageBackend(StorageBackend):
    """Grava em MEDIA_ROOT; os arquivos são servidos pelo StaticFiles montado
    em MEDIA_BASE_URL (ver app/main.py)."""

    def __init__(self, root: str, base_url: str) -> None:
        self._root = Path(root)
        self._base_url = base_url.rstrip("/")

    def _resolve(self, key: str) -> Path:
        # `key` é sempre gerada pelo próprio servidor (uuid4 + extensão
        # controlada) — nunca a partir de input do cliente — então não há
        # necessidade (nem risco) de path traversal aqui, mas resolvemos
        # dentro de `root` mesmo assim por defesa em profundidade.
        path = (self._root / key).resolve()
        if self._root.resolve() not in path.parents and path != self._root.resolve():
            raise ValueError("Chave de armazenamento inválida")
        return path

    def save(self, data: bytes, key: str) -> None:
        path = self._resolve(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def delete(self, key: str) -> None:
        path = self._resolve(key)
        path.unlink(missing_ok=True)

    def url_for(self, key: str) -> str:
        return f"{self._base_url}/{key}"


def get_storage_backend() -> StorageBackend:
    if settings.STORAGE_BACKEND == "local":
        return LocalStorageBackend(settings.MEDIA_ROOT, settings.MEDIA_BASE_URL)
    # Ponto de extensão para o deploy futuro, ex.:
    #   if settings.STORAGE_BACKEND == "s3":
    #       return S3StorageBackend(bucket=settings.S3_BUCKET, ...)
    raise ValueError(f"STORAGE_BACKEND desconhecido: {settings.STORAGE_BACKEND!r}")


storage = get_storage_backend()
