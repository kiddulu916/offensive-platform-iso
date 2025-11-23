"""JSON result aggregator for final workflow output"""
from typing import Dict, Any, List
import json
from pathlib import Path
from datetime import datetime, UTC
from app.core.logging_config import get_workflow_logger

class JsonAggregatorProcessor:
    """Processor for aggregating workflow results into final JSON report"""

    def execute(self, task, previous_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute JSON aggregation task

        Args:
            task: WorkflowTask with parameters:
                - output_file: Path to output JSON file
                - sections: List of sections to include, each with:
                    - name: Section name in output JSON
                    - source_task: Task ID to pull data from
                    - source_field: Field in source task results
                    - optional: If True, skip if source not found (default: False)
                - include_metadata: Include metadata section (default: True)
            previous_results: Previous task results

        Returns:
            Dictionary with success status and output file path
        """
        logger = get_workflow_logger(task_id=task.task_id, tool="json_aggregator")

        try:
            params = task.parameters
            output_file = Path(params.get("output_file"))
            sections_config = params.get("sections", [])
            include_metadata = params.get("include_metadata", True)

            logger.info(f"Starting JSON aggregation: {len(sections_config)} sections to {output_file}")

            # Build aggregated result
            aggregated = {}

            # Add metadata
            if include_metadata:
                aggregated["metadata"] = {
                    "generated_at": datetime.now(UTC).isoformat(),
                    "workflow_id": task.task_id,
                    "total_sections": len(sections_config)
                }

            # Add each configured section
            for section_config in sections_config:
                section_name = section_config.get("name")
                source_task = section_config.get("source_task")
                source_field = section_config.get("source_field")
                optional = section_config.get("optional", False)

                if source_task not in previous_results:
                    if not optional:
                        return {
                            "success": False,
                            "error": f"Required source task '{source_task}' not found"
                        }
                    continue

                source_data = previous_results[source_task]

                if source_field not in source_data:
                    if not optional:
                        return {
                            "success": False,
                            "error": f"Field '{source_field}' not found in task '{source_task}'"
                        }
                    continue

                aggregated[section_name] = source_data[source_field]

            # Write to file
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, 'w') as f:
                json.dump(aggregated, f, indent=2)

            sections_written = len(aggregated) - (1 if include_metadata else 0)
            logger.info(f"JSON aggregation complete: {sections_written} sections written to {output_file}")

            return {
                "success": True,
                "output_file": str(output_file),
                "sections_written": sections_written
            }

        except Exception as e:
            logger.error(f"JSON aggregation failed: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
