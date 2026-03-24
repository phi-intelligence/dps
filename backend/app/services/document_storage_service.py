"""
Pluggable binary document storage. Routes must not embed filesystem paths.

Supports local filesystem and S3-compatible object stores (AWS S3, MinIO, etc.).
"""
from __future__ import annotations

import hashlib
import io
import os
import uuid
from abc import ABC, abstractmethod
from pathlib import Path
from typing import BinaryIO, Literal

from backend.app.core.config import settings

StorageProviderName = Literal["local", "s3"]


def build_storage_key(
    *,
    document_type: str,
    document_id: str,
    filename_safe: str,
    unique_token: str | None = None,
) -> str:
    """
    Opaque storage key (not a full path). Includes a unique token so regenerated
    PDFs never overwrite prior binaries (audit / versioning).
    """
    ext = Path(filename_safe).suffix[:16] or ".bin"
    tok = unique_token or uuid.uuid4().hex[:12]
    if ".." in document_type or "/" in document_type:
        raise ValueError("Invalid document_type for key")
    return f"{document_type}/{document_id[:2]}/{document_id}/{tok}{ext}"


class DocumentStorageBackend(ABC):
    @abstractmethod
    def save(self, *, storage_key: str, data: bytes) -> None:
        pass

    @abstractmethod
    def open_read(self, *, storage_key: str) -> BinaryIO:
        pass

    @abstractmethod
    def exists(self, *, storage_key: str) -> bool:
        pass

    @abstractmethod
    def delete(self, *, storage_key: str) -> None:
        pass


class LocalFilesystemStorage(DocumentStorageBackend):
    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, storage_key: str) -> Path:
        if ".." in storage_key or storage_key.startswith("/"):
            raise ValueError("Invalid storage key")
        return self.root / storage_key

    def save(self, *, storage_key: str, data: bytes) -> None:
        path = self._path(storage_key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def open_read(self, *, storage_key: str) -> BinaryIO:
        return self._path(storage_key).open("rb")

    def exists(self, *, storage_key: str) -> bool:
        return self._path(storage_key).is_file()

    def delete(self, *, storage_key: str) -> None:
        p = self._path(storage_key)
        if p.is_file():
            p.unlink()


class S3CompatibleStorage(DocumentStorageBackend):
    """
    S3-compatible object storage. Pass `client` in tests to inject a mock.
    """

    def __init__(
        self,
        *,
        bucket: str,
        prefix: str = "",
        client: object | None = None,
    ) -> None:
        if not bucket:
            raise ValueError("S3 bucket is required when using S3 storage")
        self.bucket = bucket
        self.prefix = (prefix or "").strip().strip("/")
        self._client = client if client is not None else _build_boto3_s3_client()

    def _full_key(self, storage_key: str) -> str:
        if ".." in storage_key or storage_key.startswith("/"):
            raise ValueError("Invalid storage key")
        if self.prefix:
            return f"{self.prefix}/{storage_key}"
        return storage_key

    def save(self, *, storage_key: str, data: bytes) -> None:
        key = self._full_key(storage_key)
        self._client.put_object(Bucket=self.bucket, Key=key, Body=data)

    def open_read(self, *, storage_key: str) -> BinaryIO:
        key = self._full_key(storage_key)
        resp = self._client.get_object(Bucket=self.bucket, Key=key)
        body = resp["Body"].read()
        return io.BytesIO(body)

    def exists(self, *, storage_key: str) -> bool:
        from botocore.exceptions import ClientError

        key = self._full_key(storage_key)
        try:
            self._client.head_object(Bucket=self.bucket, Key=key)
            return True
        except ClientError as e:
            code = e.response.get("Error", {}).get("Code", "")
            if code in ("404", "NoSuchKey", "NotFound"):
                return False
            if e.response.get("ResponseMetadata", {}).get("HTTPStatusCode") == 404:
                return False
            raise

    def delete(self, *, storage_key: str) -> None:
        key = self._full_key(storage_key)
        self._client.delete_object(Bucket=self.bucket, Key=key)

    def get_presigned_download_url(self, *, storage_key: str, expires_in: int | None = None) -> str:
        """
        Internal use only (e.g. future async workers). App-mediated downloads stay default.
        """
        key = self._full_key(storage_key)
        ttl = expires_in if expires_in is not None else int(settings.PHI_DPS_S3_PRESIGNED_TTL_SECONDS)
        return self._client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": key},
            ExpiresIn=ttl,
        )


def _build_boto3_s3_client():  # type: ignore[no-untyped-def]
    import boto3
    from botocore.config import Config as BotoConfig

    addr = (getattr(settings, "PHI_DPS_S3_ADDRESSING_STYLE", None) or "path").lower()
    s3_addr = "path" if addr == "path" else "virtual"
    bcfg = BotoConfig(signature_version="s3v4", s3={"addressing_style": s3_addr})

    kwargs: dict = {
        "region_name": settings.PHI_DPS_S3_REGION,
        "config": bcfg,
    }
    if settings.PHI_DPS_S3_ENDPOINT_URL:
        kwargs["endpoint_url"] = settings.PHI_DPS_S3_ENDPOINT_URL
    ak = settings.PHI_DPS_S3_ACCESS_KEY_ID or os.getenv("AWS_ACCESS_KEY_ID")
    sk = settings.PHI_DPS_S3_SECRET_ACCESS_KEY or os.getenv("AWS_SECRET_ACCESS_KEY")
    if ak and sk:
        kwargs["aws_access_key_id"] = ak
        kwargs["aws_secret_access_key"] = sk
    return boto3.client("s3", **kwargs)


def get_storage_provider_name() -> StorageProviderName:
    v = (
        getattr(settings, "PHI_DPS_DOCUMENT_STORAGE_PROVIDER", None)
        or os.getenv("PHI_DPS_DOCUMENT_STORAGE_PROVIDER", "local")
    ).lower()
    if v in ("local", "filesystem"):
        return "local"
    if v == "s3":
        return "s3"
    return "local"


def get_storage_backend() -> DocumentStorageBackend:
    name = get_storage_provider_name()
    if name == "local":
        root = Path(settings.PHI_DPS_DOCUMENT_STORAGE_ROOT)
        if not root.is_absolute():
            root = Path.cwd() / root
        return LocalFilesystemStorage(root)
    if name == "s3":
        bucket = getattr(settings, "PHI_DPS_S3_BUCKET", "") or ""
        prefix = getattr(settings, "PHI_DPS_S3_PREFIX", "") or ""
        return S3CompatibleStorage(bucket=bucket, prefix=prefix)
    raise RuntimeError(f"Unknown storage provider: {name}")


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def save_binary(*, storage_key: str, data: bytes) -> None:
    get_storage_backend().save(storage_key=storage_key, data=data)


def stream_document(*, storage_key: str) -> BinaryIO:
    return get_storage_backend().open_read(storage_key=storage_key)


def document_exists(*, storage_key: str) -> bool:
    return get_storage_backend().exists(storage_key=storage_key)


def delete_document(*, storage_key: str) -> None:
    get_storage_backend().delete(storage_key=storage_key)
