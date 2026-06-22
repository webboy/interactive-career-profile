from app.core.config import Settings, get_settings
from app.services.storage.base import StorageDriver
from app.services.storage.local import LocalStorageDriver


class UnsupportedStorageDriverError(Exception):
    pass


def get_storage_driver(settings: Settings | None = None) -> StorageDriver:
    config = settings or get_settings()
    driver_name = config.filesystem_driver.lower()

    if driver_name == "local":
        return LocalStorageDriver(config.local_storage_path)

    if driver_name in {"s3", "s3-compatible"}:
        raise UnsupportedStorageDriverError(
            "S3-compatible storage is configured but not implemented yet."
        )

    raise UnsupportedStorageDriverError(f"Unsupported filesystem driver: {driver_name}")
