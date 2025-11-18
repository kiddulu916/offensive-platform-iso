"""Metasploit Framework adapter for exploitation"""
from app.tools.base import BaseTool, ToolMetadata, ToolCategory
from typing import Dict, Any, List
import tempfile
import re
import os


class MetasploitAdapter(BaseTool):

    def get_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="metasploit",
            category=ToolCategory.EXPLOITATION,
            description="Metasploit Framework for exploitation and post-exploitation",
            executable="msfconsole",
            requires_root=False,
            default_timeout=900
        )

    def validate_parameters(self, params: Dict[str, Any]) -> bool:
        """Validate that module is specified"""
        return "module" in params

    def build_command(self, params: Dict[str, Any]) -> List[str]:
        """Build msfconsole command with module and options"""
        module = params["module"]

        # Build MSF commands
        commands = [f"use {module}"]

        # Set payload if specified
        if "payload" in params:
            commands.append(f"set PAYLOAD {params['payload']}")

        # Set all other options (excluding module and payload)
        for key, value in params.items():
            if key not in ["module", "payload", "timeout"]:
                # Convert to MSF option format (uppercase)
                msf_key = key.upper()
                commands.append(f"set {msf_key} {value}")

        # Run the module
        if "exploit" in module:
            commands.append("exploit")
        else:
            commands.append("run")

        # Exit after execution
        commands.append("exit")

        # Build command string
        command_string = "; ".join(commands)

        # Return msfconsole with quiet mode and execute commands
        cmd = [
            self.metadata.executable,
            "-q",  # Quiet mode (no banner)
            "-x", command_string  # Execute commands
        ]

        return cmd

    def parse_output(self, output: str, stderr: str, return_code: int) -> Dict[str, Any]:
        """Parse Metasploit console output"""
        findings = []
        sessions = []
        session_opened = False

        # Extract findings (lines starting with [+])
        for line in output.split('\n'):
            line = line.strip()

            if line.startswith('[+]'):
                findings.append(line[3:].strip())

            # Detect session openings
            if 'session' in line.lower() and 'opened' in line.lower():
                session_opened = True
                # Extract session info
                session_match = re.search(r'session (\d+)', line, re.IGNORECASE)
                if session_match:
                    sessions.append({
                        "id": session_match.group(1),
                        "info": line
                    })

        return {
            "module_output": output,
            "findings": findings,
            "session_opened": session_opened,
            "sessions": sessions,
            "total_findings": len(findings)
        }
