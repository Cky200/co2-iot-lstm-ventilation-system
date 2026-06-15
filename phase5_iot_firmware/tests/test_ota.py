from __future__ import annotations

import asyncio
import hashlib
import tarfile

import pytest

from iot_firmware.ota import OTAManifest, OTAUpdater


def test_ota_manifest_version_comparison(tmp_path):
    updater = OTAUpdater(current_version="1.2.3", staging_dir=tmp_path)

    assert updater.is_newer(OTAManifest(version="1.2.4", url="https://example/fw.tgz", sha256="abc"))
    assert not updater.is_newer(OTAManifest(version="1.2.3", url="https://example/fw.tgz", sha256="abc"))


def test_ota_sha256_verification(tmp_path):
    archive = tmp_path / "firmware.tar.gz"
    archive.write_bytes(b"firmware")
    digest = hashlib.sha256(b"firmware").hexdigest()

    OTAUpdater.verify_sha256(archive, digest)

    with pytest.raises(ValueError):
        OTAUpdater.verify_sha256(archive, "0" * 64)


def test_ota_install_extracts_tar_archive(tmp_path):
    payload_dir = tmp_path / "payload"
    payload_dir.mkdir()
    (payload_dir / "version.txt").write_text("1.2.4", encoding="utf-8")
    archive = tmp_path / "firmware.tar.gz"
    with tarfile.open(archive, "w:gz") as tar:
        tar.add(payload_dir / "version.txt", arcname="version.txt")

    updater = OTAUpdater(current_version="1.2.3", staging_dir=tmp_path / "staging")
    manifest = OTAManifest(version="1.2.4", url="https://example/fw.tgz", sha256="unused")

    asyncio.run(updater.install(archive, manifest))

    assert (tmp_path / "staging" / "release-1.2.4" / "version.txt").read_text(encoding="utf-8") == "1.2.4"
