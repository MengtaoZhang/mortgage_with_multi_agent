"""
File manager with concurrent safety, storage optimization, and memory management
"""

import json
import os
import gzip
import shutil
import time
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict
from decimal import Decimal
import asyncio
import threading
from contextlib import asynccontextmanager

from src.loan_underwriter.models import LoanFile


class LoanFileManager:
    """Thread-safe loan file manager with storage optimization"""

    MAX_AUDIT_ENTRIES = 100
    MAX_FILE_SIZE_MB = 10
    MAX_TOTAL_STORAGE_GB = 5
    BACKUP_RETENTION_DAYS = 30

    def __init__(self, base_directory: str = "./loan_files"):
        self.base_directory = Path(base_directory)
        self.base_directory.mkdir(exist_ok=True)

        self.active_dir = self.base_directory / "active"
        self.archive_dir = self.base_directory / "archive"
        self.backup_dir = self.base_directory / "backups"

        self.active_dir.mkdir(exist_ok=True)
        self.archive_dir.mkdir(exist_ok=True)
        self.backup_dir.mkdir(exist_ok=True)

        self._locks: Dict[str, asyncio.Lock] = {}
        self._lock_manager = threading.Lock()
        self._write_counts: Dict[str, int] = {}
        self._last_cleanup = datetime.now()

    def _get_lock(self, loan_number: str) -> asyncio.Lock:
        with self._lock_manager:
            if loan_number not in self._locks:
                self._locks[loan_number] = asyncio.Lock()
            return self._locks[loan_number]

    @asynccontextmanager
    async def acquire_loan_lock(self, loan_number: str):
        lock = self._get_lock(loan_number)
        async with lock:
            yield

    def _custom_encoder(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        elif isinstance(obj, datetime):
            return obj.isoformat()
        elif hasattr(obj, 'dict'):
            return obj.dict()
        return str(obj)

    def _get_file_path(self, loan_number: str, archived: bool = False) -> Path:
        directory = self.archive_dir if archived else self.active_dir
        return directory / f"{loan_number}.json"

    def _rotate_audit_trail(self, loan_file: LoanFile) -> None:
        if len(loan_file.audit_trail) > self.MAX_AUDIT_ENTRIES:
            old_entries = loan_file.audit_trail[:-self.MAX_AUDIT_ENTRIES]
            loan_file.audit_trail = loan_file.audit_trail[-self.MAX_AUDIT_ENTRIES:]

            archive_path = self.archive_dir / f"{loan_file.loan_info.loan_number}_audit_archive.json.gz"

            existing_archive = []
            if archive_path.exists():
                with gzip.open(archive_path, 'rt') as f:
                    existing_archive = json.load(f)

            existing_archive.extend([e.dict() for e in old_entries])

            with gzip.open(archive_path, 'wt') as f:
                json.dump(existing_archive, f, default=self._custom_encoder)

    def _check_file_size(self, file_path: Path) -> None:
        if file_path.exists():
            size_mb = file_path.stat().st_size / (1024 * 1024)
            if size_mb > self.MAX_FILE_SIZE_MB:
                print(f"⚠️  WARNING: File {file_path.name} is {size_mb:.2f}MB")

    def _check_total_storage(self) -> None:
        total_size = sum(f.stat().st_size for f in self.base_directory.rglob('*') if f.is_file())
        total_gb = total_size / (1024 * 1024 * 1024)

        if total_gb > self.MAX_TOTAL_STORAGE_GB:
            print(f"⚠️  WARNING: Total storage is {total_gb:.2f}GB")

    def _create_backup(self, loan_number: str) -> Optional[str]:
        source = self._get_file_path(loan_number)

        if not source.exists():
            return None

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_dir / f"{loan_number}_backup_{timestamp}.json.gz"

        with open(source, 'rb') as f_in:
            with gzip.open(backup_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)

        return str(backup_path)

    def _cleanup_old_backups(self) -> None:
        cutoff_date = datetime.now() - timedelta(days=self.BACKUP_RETENTION_DAYS)

        for backup_file in self.backup_dir.glob("*_backup_*.json.gz"):
            file_time = datetime.fromtimestamp(backup_file.stat().st_mtime)
            if file_time < cutoff_date:
                backup_file.unlink()

    def save_loan_file(self, loan_file: LoanFile) -> str:
        loan_number = loan_file.loan_info.loan_number
        file_path = self._get_file_path(loan_number)

        self._rotate_audit_trail(loan_file)

        if file_path.exists():
            self._create_backup(loan_number)

        loan_data = json.loads(loan_file.model_dump_json())

        with open(file_path, 'w') as f:
            json.dump(loan_data, f, indent=2, default=self._custom_encoder)

        self._write_counts[loan_number] = self._write_counts.get(loan_number, 0) + 1
        elapsed = time.perf_counter()
        print(
            f"[WRITE] t+{elapsed:.3f}s loan={loan_number} "
            f"count={self._write_counts[loan_number]} path={file_path}"
        )

        self._check_file_size(file_path)

        if (datetime.now() - self._last_cleanup).total_seconds() > 3600:
            self._cleanup_old_backups()
            self._check_total_storage()
            self._last_cleanup = datetime.now()

        return str(file_path)

    def load_loan_file(self, loan_number: str) -> Optional[LoanFile]:
        file_path = self._get_file_path(loan_number)

        if not file_path.exists():
            file_path = self._get_file_path(loan_number, archived=True)
            if not file_path.exists():
                return None

        with open(file_path, 'r') as f:
            loan_data = json.load(f)

        loan_file = LoanFile(**loan_data)
        return loan_file

    def list_loan_files(self) -> list:
        return [f.stem for f in self.active_dir.glob("*.json")]

    def get_storage_stats(self) -> Dict:
        stats = {
            "active_files": len(list(self.active_dir.glob("*.json"))),
            "archived_files": len(list(self.archive_dir.glob("*.json.gz"))),
            "backup_files": len(list(self.backup_dir.glob("*.json.gz"))),
            "total_size_mb": 0,
            "active_size_mb": 0,
            "archive_size_mb": 0,
            "backup_size_mb": 0
        }

        for directory, key in [
            (self.active_dir, "active_size_mb"),
            (self.archive_dir, "archive_size_mb"),
            (self.backup_dir, "backup_size_mb")
        ]:
            size = sum(f.stat().st_size for f in directory.rglob('*') if f.is_file())
            stats[key] = size / (1024 * 1024)
            stats["total_size_mb"] += stats[key]

        return stats

    def get_write_count(self, loan_number: str) -> int:
        """Get the total number of writes for a specific loan"""
        return self._write_counts.get(loan_number, 0)

    def print_storage_stats(self) -> None:
        stats = self.get_storage_stats()

        print("\n" + "="*60)
        print("📊 STORAGE STATISTICS")
        print("="*60)
        print(f"Active Files: {stats['active_files']}")
        print(f"Archived Files: {stats['archived_files']}")
        print(f"Backup Files: {stats['backup_files']}")
        print(f"\nActive Storage: {stats['active_size_mb']:.2f} MB")
        print(f"Archive Storage: {stats['archive_size_mb']:.2f} MB")
        print(f"Backup Storage: {stats['backup_size_mb']:.2f} MB")
        print(f"Total Storage: {stats['total_size_mb']:.2f} MB")

        # Show write statistics
        if self._write_counts:
            print(f"\n📝 WRITE STATISTICS:")
            for loan_num, count in sorted(self._write_counts.items()):
                print(f"  {loan_num}: {count} writes")

        print("="*60 + "\n")


# ========== SINGLETON INSTANCE ==========
# Create a single shared instance to ensure consistent write tracking
# across all modules. Import this instance, not the class!
_file_manager_instance = None

def get_file_manager() -> LoanFileManager:
    """Get the singleton file manager instance"""
    global _file_manager_instance
    if _file_manager_instance is None:
        _file_manager_instance = LoanFileManager()
    return _file_manager_instance

# Export the singleton instance
file_manager = get_file_manager()

# Map alternative module paths to the same instance to avoid duplicate singletons
sys.modules.setdefault("src.loan_underwriter.file_manager", sys.modules[__name__])
sys.modules.setdefault("loan_underwriter.file_manager", sys.modules[__name__])

__all__ = ['LoanFileManager', 'file_manager', 'get_file_manager']
