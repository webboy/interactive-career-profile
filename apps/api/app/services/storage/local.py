from pathlib import Path

from app.services.storage.base import StorageDriver


class LocalStorageDriver:
    def __init__(self, base_path: str) -> None:
        self.base_path = Path(base_path)

    def _resolve(self, path: str) -> Path:
        normalized = path.lstrip("/")
        full_path = (self.base_path / normalized).resolve()
        base_resolved = self.base_path.resolve()
        if not str(full_path).startswith(str(base_resolved)):
            raise ValueError("Invalid storage path")
        return full_path

    def save(self, path: str, content: bytes) -> str:
        full_path = self._resolve(path)
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_bytes(content)
        return path

    def read(self, path: str) -> bytes:
        full_path = self._resolve(path)
        return full_path.read_bytes()

    def delete(self, path: str) -> None:
        full_path = self._resolve(path)
        if full_path.exists():
            full_path.unlink()

    def exists(self, path: str) -> bool:
        return self._resolve(path).exists()


def ensure_storage_driver(driver: object) -> StorageDriver:
    if not isinstance(driver, LocalStorageDriver):
        raise TypeError("Unsupported storage driver instance")
    return driver
