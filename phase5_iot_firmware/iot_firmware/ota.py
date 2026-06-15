"""Over-the-air firmware update support."""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import shutil
import tarfile
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from packaging.version import Version

try:
    import aiohttp
except ImportError:  # pragma: no cover - dependency path
    aiohttp = None  # type: ignore[assignment]


@dataclass(frozen=True)
class OTAManifest:
    version: str
    url: str
    sha256: str
    install_command: list[str] | None = None

    @classmethod
    def from_json(cls, payload: str | dict[str, Any]) -> "OTAManifest":
        data = json.loads(payload) if isinstance(payload, str) else payload
        return cls(
            version=str(data["version"]),
            url=str(data["url"]),
            sha256=str(data["sha256"]),
            install_command=list(data["install_command"]) if data.get("install_command") else None,
        )


class OTAUpdater:
    def __init__(
        self,
        *,
        current_version: str,
        staging_dir: Path,
        logger: logging.Logger | None = None,
    ) -> None:
        self.current_version = current_version
        self.staging_dir = staging_dir
        self.logger = logger or logging.getLogger(__name__)

    def is_newer(self, manifest: OTAManifest) -> bool:
        return Version(manifest.version) > Version(self.current_version)

    async def fetch_manifest(self, manifest_url: str) -> OTAManifest:
        if aiohttp is None:
            raise RuntimeError("aiohttp is required for OTA support")
        async with aiohttp.ClientSession() as session:
            async with session.get(manifest_url, timeout=20) as response:
                response.raise_for_status()
                return OTAManifest.from_json(await response.text())

    async def apply_if_available(self, manifest_url: str) -> bool:
        manifest = await self.fetch_manifest(manifest_url)
        if not self.is_newer(manifest):
            self.logger.info("Firmware is current: %s", self.current_version)
            return False
        archive_path = await self.download(manifest)
        self.verify_sha256(archive_path, manifest.sha256)
        await self.install(archive_path, manifest)
        return True

    async def download(self, manifest: OTAManifest) -> Path:
        self.staging_dir.mkdir(parents=True, exist_ok=True)
        filename = Path(urlparse(manifest.url).path).name or f"firmware-{manifest.version}.tar.gz"
        target = self.staging_dir / filename
        tmp_target = target.with_suffix(target.suffix + ".part")

        if aiohttp is None:
            raise RuntimeError("aiohttp is required for OTA support")
        async with aiohttp.ClientSession() as session:
            async with session.get(manifest.url, timeout=120) as response:
                response.raise_for_status()
                with tmp_target.open("wb") as handle:
                    async for chunk in response.content.iter_chunked(1024 * 64):
                        handle.write(chunk)
        tmp_target.replace(target)
        return target

    @staticmethod
    def verify_sha256(path: Path, expected_hash: str) -> None:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        actual = digest.hexdigest()
        if actual.lower() != expected_hash.lower():
            raise ValueError(f"OTA SHA-256 mismatch: expected {expected_hash}, got {actual}")

    async def install(self, archive_path: Path, manifest: OTAManifest) -> None:
        extract_dir = self.staging_dir / f"release-{manifest.version}"
        if extract_dir.exists():
            shutil.rmtree(extract_dir)
        extract_dir.mkdir(parents=True)

        await asyncio.to_thread(self._extract_archive, archive_path, extract_dir)
        if manifest.install_command:
            process = await asyncio.create_subprocess_exec(
                *manifest.install_command,
                cwd=extract_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await process.communicate()
            if process.returncode != 0:
                raise RuntimeError(
                    "OTA install command failed "
                    f"rc={process.returncode} stdout={stdout.decode()} stderr={stderr.decode()}"
                )

    @staticmethod
    def _extract_archive(archive_path: Path, extract_dir: Path) -> None:
        if zipfile.is_zipfile(archive_path):
            with zipfile.ZipFile(archive_path) as archive:
                archive.extractall(extract_dir)
            return
        if tarfile.is_tarfile(archive_path):
            with tarfile.open(archive_path) as archive:
                for member in archive.getmembers():
                    target = (extract_dir / member.name).resolve()
                    if not str(target).startswith(str(extract_dir.resolve())):
                        raise ValueError(f"Unsafe OTA archive member: {member.name}")
                archive.extractall(extract_dir)
            return
        raise ValueError(f"Unsupported OTA archive format: {archive_path}")
