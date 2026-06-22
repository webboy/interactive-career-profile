from typing import Protocol


class StorageDriver(Protocol):
    def save(self, path: str, content: bytes) -> str:
        """Save content and return the storage path."""

    def read(self, path: str) -> bytes:
        """Read stored content."""

    def delete(self, path: str) -> None:
        """Delete stored content."""

    def exists(self, path: str) -> bool:
        """Return whether stored content exists."""
