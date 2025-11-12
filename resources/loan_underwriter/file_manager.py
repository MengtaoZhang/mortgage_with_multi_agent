"""
File manager for saving and loading loan files as JSON
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Optional
from decimal import Decimal

from models import LoanFile


class LoanFileManager:
    """Manages loan file persistence"""

    def __init__(self, base_directory: str = "./loan_files"):
        """Initialize file manager"""
        self.base_directory = Path(base_directory)
        self.base_directory.mkdir(exist_ok=True)

    def _custom_encoder(self, obj):
        """Custom JSON encoder for special types"""
        if isinstance(obj, Decimal):
            return float(obj)
        elif isinstance(obj, (datetime,)):
            return obj.isoformat()
        elif hasattr(obj, 'dict'):
            return obj.dict()
        return str(obj)

    def save_loan_file(self, loan_file: LoanFile) -> str:
        """
        Save loan file to disk as JSON

        Returns: file path
        """
        loan_number = loan_file.loan_info.loan_number
        file_path = self.base_directory / f"{loan_number}.json"

        # Convert to dict and save
        loan_data = json.loads(loan_file.model_dump_json())

        with open(file_path, 'w') as f:
            json.dump(loan_data, f, indent=2, default=self._custom_encoder)

        print(f"✅ Loan file saved: {file_path}")
        return str(file_path)

    def load_loan_file(self, loan_number: str) -> Optional[LoanFile]:
        """
        Load loan file from disk

        Returns: LoanFile or None if not found
        """
        file_path = self.base_directory / f"{loan_number}.json"

        if not file_path.exists():
            print(f"❌ Loan file not found: {file_path}")
            return None

        with open(file_path, 'r') as f:
            loan_data = json.load(f)

        loan_file = LoanFile(**loan_data)
        print(f"✅ Loan file loaded: {file_path}")
        return loan_file

    def list_loan_files(self) -> list:
        """List all loan files"""
        return [f.stem for f in self.base_directory.glob("*.json")]

    def delete_loan_file(self, loan_number: str) -> bool:
        """Delete loan file"""
        file_path = self.base_directory / f"{loan_number}.json"
        if file_path.exists():
            file_path.unlink()
            print(f"✅ Loan file deleted: {file_path}")
            return True
        return False

    def backup_loan_file(self, loan_number: str) -> str:
        """Create timestamped backup"""
        source = self.base_directory / f"{loan_number}.json"
        if not source.exists():
            raise FileNotFoundError(f"Loan file {loan_number} not found")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.base_directory / f"{loan_number}_backup_{timestamp}.json"

        import shutil
        shutil.copy(source, backup_path)
        print(f"✅ Backup created: {backup_path}")
        return str(backup_path)