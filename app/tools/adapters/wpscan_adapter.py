"""WPScan tool adapter for WordPress security scanning"""
from app.tools.base import BaseTool, ToolMetadata, ToolCategory
from typing import Dict, Any, List
import json


class WpscanAdapter(BaseTool):

    def get_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="wpscan",
            category=ToolCategory.SCANNING,
            description="WordPress security scanner",
            executable="wpscan",
            requires_root=False,
            default_timeout=600
        )

    def validate_parameters(self, params: Dict[str, Any]) -> bool:
        """Validate that url is provided"""
        return "url" in params

    def build_command(self, params: Dict[str, Any]) -> List[str]:
        """Build wpscan command"""
        cmd = [self.metadata.executable]

        # Target URL
        cmd.extend(["--url", params["url"]])

        # JSON output format
        cmd.extend(["--format", "json"])

        # API token (optional but recommended for vulnerability data)
        if "api_token" in params:
            cmd.extend(["--api-token", params["api_token"]])

        # Enumeration options
        if "enumerate" in params:
            enums = params["enumerate"]
            if isinstance(enums, list):
                cmd.extend(["--enumerate", ",".join(enums)])
            else:
                cmd.extend(["--enumerate", enums])

        # Detection mode
        if "detection_mode" in params:
            cmd.extend(["--detection-mode", params["detection_mode"]])

        # Disable banner
        cmd.append("--no-banner")

        return cmd

    def parse_output(self, output: str, stderr: str, return_code: int) -> Dict[str, Any]:
        """Parse WPScan JSON output"""
        plugins = []
        themes = []
        vulnerabilities = []
        wordpress_version = None

        if not output.strip():
            return {
                "wordpress_version": wordpress_version,
                "plugins": plugins,
                "themes": themes,
                "vulnerabilities": vulnerabilities,
                "total_vulnerabilities": 0
            }

        try:
            data = json.loads(output)

            # Extract WordPress version
            if "version" in data and data["version"]:
                version_info = data["version"]
                if isinstance(version_info, dict) and "number" in version_info:
                    wordpress_version = version_info["number"]

            # Extract plugins
            if "plugins" in data:
                for slug, plugin_data in data["plugins"].items():
                    plugin_info = {
                        "slug": slug,
                        "version": plugin_data.get("version", {}).get("number", "unknown")
                    }

                    # Extract vulnerabilities for this plugin
                    if "vulnerabilities" in plugin_data:
                        for vuln in plugin_data["vulnerabilities"]:
                            vulnerabilities.append({
                                "type": "plugin",
                                "component": slug,
                                "title": vuln.get("title", "Unknown vulnerability"),
                                "references": vuln.get("references", {})
                            })

                    plugins.append(plugin_info)

            # Extract themes
            if "themes" in data:
                for slug, theme_data in data["themes"].items():
                    theme_info = {
                        "slug": slug,
                        "version": theme_data.get("version", {}).get("number", "unknown")
                    }

                    # Extract vulnerabilities for this theme
                    if "vulnerabilities" in theme_data:
                        for vuln in theme_data["vulnerabilities"]:
                            vulnerabilities.append({
                                "type": "theme",
                                "component": slug,
                                "title": vuln.get("title", "Unknown vulnerability"),
                                "references": vuln.get("references", {})
                            })

                    themes.append(theme_info)

        except json.JSONDecodeError:
            # Return empty results on parse failure
            pass

        return {
            "wordpress_version": wordpress_version,
            "plugins": plugins,
            "themes": themes,
            "vulnerabilities": vulnerabilities,
            "total_vulnerabilities": len(vulnerabilities)
        }
