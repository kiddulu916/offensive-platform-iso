"""Utilities for result processing, deduplication, and file I/O"""
from typing import List, Dict, Any, Set
from pathlib import Path
import json

def deduplicate_subdomains(subdomains: List[Dict[str, Any]], merge_ips: bool = True) -> List[Dict[str, Any]]:
    """
    Deduplicate subdomain list by name, optionally merging IP addresses

    Args:
        subdomains: List of subdomain dictionaries with 'name' and 'ips' keys
        merge_ips: If True, merge IP lists for duplicate subdomains

    Returns:
        Deduplicated list of subdomains
    """
    seen = {}

    for subdomain in subdomains:
        name = subdomain.get("name")
        if not name:
            continue

        if name in seen:
            if merge_ips and "ips" in subdomain:
                # Merge IP addresses
                existing_ips = set(seen[name].get("ips", []))
                new_ips = set(subdomain.get("ips", []))
                seen[name]["ips"] = list(existing_ips | new_ips)

                # Merge sources
                existing_source = seen[name].get("source", "")
                new_source = subdomain.get("source", "")
                if new_source and new_source not in existing_source:
                    seen[name]["source"] = f"{existing_source},{new_source}" if existing_source else new_source
        else:
            seen[name] = subdomain.copy()

    return list(seen.values())

def merge_subdomain_lists(lists: List[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    """
    Merge multiple subdomain lists with deduplication

    Args:
        lists: List of subdomain lists to merge

    Returns:
        Merged and deduplicated subdomain list
    """
    combined = []
    for sublist in lists:
        combined.extend(sublist)

    return deduplicate_subdomains(combined, merge_ips=True)

def save_list_to_file(items: List[str], filepath: Path, append: bool = False) -> bool:
    """
    Save list of strings to text file (one per line)

    Args:
        items: List of strings to save
        filepath: Path to output file
        append: If True, append to existing file

    Returns:
        True if file was saved successfully, False on error
    """
    try:
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        mode = 'a' if append else 'w'
        with open(filepath, mode) as f:
            for item in items:
                f.write(f"{item}\n")
        return True
    except (OSError, IOError) as e:
        return False

def load_list_from_file(filepath: Path) -> List[str]:
    """
    Load list of strings from text file

    Args:
        filepath: Path to input file

    Returns:
        List of strings (one per line, stripped)
    """
    filepath = Path(filepath)
    if not filepath.exists():
        return []

    with open(filepath, 'r') as f:
        return [line.strip() for line in f if line.strip()]

def extract_ips_from_results(results: Dict[str, Any], key: str = "hosts") -> List[str]:
    """
    Extract IP addresses from scan results

    Args:
        results: Result dictionary from tool execution
        key: Key containing host data (default: "hosts")

    Returns:
        List of unique IP addresses
    """
    ips = set()

    if key in results:
        for host in results[key]:
            if "ip" in host:
                ips.add(host["ip"])

    return list(ips)

def extract_subdomains_from_results(results: Dict[str, Any], key: str = "subdomains") -> List[str]:
    """
    Extract subdomain names from scan results

    Args:
        results: Result dictionary from tool execution
        key: Key containing subdomain data

    Returns:
        List of subdomain names
    """
    subdomains = []

    if key in results:
        for item in results[key]:
            if isinstance(item, dict) and "name" in item:
                subdomains.append(item["name"])
            elif isinstance(item, str):
                subdomains.append(item)

    return subdomains
