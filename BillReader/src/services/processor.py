import shutil
import csv
import logging
from datetime import datetime
from pathlib import Path

from src.services.file_parser import FileParserService
from src.services.validation_service import ValidationService

logger = logging.getLogger(__name__)

class BillProcessor:
    def __init__(self, file_parser: FileParserService, validation_service: ValidationService):
        self.parser = file_parser
        self.validator = validation_service

    def process_directories(self, prev_month_dir: str, curr_month_dir: str, checked_dir: str, manual_review_dir: str, progress_callback=None) -> str:
        """
        Matches files, validates them, routes to respective folders, and generates a report.
        """
        # Idempotency: creating output dirs if they don't exist
        out_path = Path(checked_dir).parent
        
        manual_review_path = Path(manual_review_dir)
        checked_path = Path(checked_dir)
        
        manual_review_path.mkdir(parents=True, exist_ok=True)
        checked_path.mkdir(parents=True, exist_ok=True)
        
        report_filename = f"reconciliation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        report_path = out_path / report_filename
        report_data = []

        # File Matching
        prev_map = self.parser.map_files_by_consumer(prev_month_dir)
        curr_map = self.parser.map_files_by_consumer(curr_month_dir)
        
        all_consumers = set(prev_map.keys()).union(set(curr_map.keys()))
        total_files = len(all_consumers)
        processed_count = 0

        for consumer in all_consumers:
            processed_count += 1
            if progress_callback:
                progress_callback(processed_count, total_files)
            prev_file = prev_map.get(consumer)
            curr_file = curr_map.get(consumer)
            
            # Basic validation: Handle missing files
            if not prev_file or not curr_file:
                reason = "Missing file for previous month." if curr_file else "Missing file for current month."
                
                # If current file exists but no previous reference, route it to manual review
                if curr_file:
                    dest = self._route_file(curr_file, manual_review_path)
                    report_data.append({"ConsumerNumber": consumer, "Status": "Manual Review", "Reason": reason, "File": str(dest)})
                else:
                    report_data.append({"ConsumerNumber": consumer, "Status": "Missing Inputs", "Reason": reason, "File": prev_file or "None"})
                continue
                
            try:
                # Load Excel files
                prev_df = self.parser.parse_excel(prev_file)
                curr_df = self.parser.parse_excel(curr_file)
                
                # Check business rules
                is_valid, reason = self.validator.validate_consumer_records(prev_df, curr_df)
                
                if is_valid:
                    dest = self._route_file(curr_file, checked_path)
                    report_data.append({"ConsumerNumber": consumer, "Status": "Checked", "Reason": reason, "File": str(dest)})
                else:
                    dest = self._route_file(curr_file, manual_review_path)
                    report_data.append({"ConsumerNumber": consumer, "Status": "Manual Review", "Reason": reason, "File": str(dest)})
            except Exception as e:
                logger.error(f"Error processing consumer {consumer}: {e}")
                # Corrupted files go to manual review
                if curr_file:
                    dest = self._route_file(curr_file, manual_review_path)
                    report_data.append({"ConsumerNumber": consumer, "Status": "Manual Review", "Reason": f"Parsing Error: {str(e)}", "File": str(dest)})
                
        # Generate Log Report
        self._write_report(report_path, report_data)
        return str(report_path)

    def _route_file(self, src: str, dest_dir: Path) -> Path:
        """
        Moves file to output directory.
        Uses shutil.move but replaces if exists for idempotency.
        """
        src_path = Path(src)
        dest_path = dest_dir / src_path.name
        
        # Copy the file instead of moving it
        if src_path.exists():
            shutil.copy2(str(src_path), str(dest_path))
            
        return dest_path
        
    def _write_report(self, path: Path, data: list):
        if not data:
            return
        fields = ["ConsumerNumber", "Status", "Reason", "File"]
        with open(path, "w", newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fields)
            writer.writeheader()
            for row in data:
                writer.writerow(row)
