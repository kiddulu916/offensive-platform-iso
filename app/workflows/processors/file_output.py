"""File output processor for saving workflow results to files"""
from typing import Dict, Any, List
from pathlib import Path
import json
from app.utils.result_utils import save_list_to_file

class FileOutputProcessor:
    """Processor for saving workflow results to text files"""

    def execute(self, task, previous_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute file output task

        Args:
            task: WorkflowTask with parameters:
                - source_task: Task ID to get data from
                - source_field: Field in source task results
                - output_file: Path to output file
                - extract_field: Optional field to extract from objects (e.g., "name" or "ip")
                - format: Optional format ("txt" or "json", default: "txt")
            previous_results: Dictionary of previous task results

        Returns:
            Result dictionary with success status and file path
        """
        try:
            params = task.parameters

            # Get source data
            source_task = params.get("source_task")
            source_field = params.get("source_field")

            if source_task not in previous_results:
                return {
                    "success": False,
                    "error": f"Source task '{source_task}' not found in previous results"
                }

            source_data = previous_results[source_task]

            if source_field not in source_data:
                return {
                    "success": False,
                    "error": f"Field '{source_field}' not found in source task results"
                }

            data = source_data[source_field]

            # Extract field if specified (e.g., extract "name" from list of dicts)
            extract_field = params.get("extract_field")
            if extract_field:
                if isinstance(data, list):
                    data = [
                        item[extract_field] if isinstance(item, dict) else item
                        for item in data
                        if (isinstance(item, dict) and extract_field in item) or not isinstance(item, dict)
                    ]

            # Ensure data is a list
            if not isinstance(data, list):
                data = [data]

            # Get output file path
            output_file = Path(params.get("output_file"))
            output_format = params.get("format", "txt")

            # Save based on format
            if output_format == "json":
                output_file.parent.mkdir(parents=True, exist_ok=True)
                with open(output_file, 'w') as f:
                    json.dump(data, f, indent=2)
            else:  # txt format
                # Convert all items to strings
                string_items = [str(item) for item in data]
                save_list_to_file(string_items, output_file)

            return {
                "success": True,
                "output_file": str(output_file),
                "items_written": len(data)
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
