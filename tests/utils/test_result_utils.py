import pytest
from app.utils.result_utils import (
    deduplicate_subdomains,
    merge_subdomain_lists,
    save_list_to_file,
    load_list_from_file,
    extract_ips_from_results
)

def test_deduplicate_subdomains():
    subdomains = [
        {"name": "www.example.com", "ips": ["1.1.1.1"]},
        {"name": "mail.example.com", "ips": ["2.2.2.2"]},
        {"name": "www.example.com", "ips": ["3.3.3.3"]},  # Duplicate
    ]

    result = deduplicate_subdomains(subdomains, merge_ips=True)
    assert len(result) == 2

    # Check that IPs were merged for www.example.com
    www_entry = next(s for s in result if s["name"] == "www.example.com")
    assert set(www_entry["ips"]) == {"1.1.1.1", "3.3.3.3"}

def test_merge_subdomain_lists():
    list1 = [{"name": "www.example.com", "ips": ["1.1.1.1"], "source": "amass"}]
    list2 = [{"name": "mail.example.com", "ips": ["2.2.2.2"], "source": "subfinder"}]
    list3 = [{"name": "www.example.com", "ips": ["3.3.3.3"], "source": "sublist3r"}]

    result = merge_subdomain_lists([list1, list2, list3])
    assert len(result) == 2

    www_entry = next(s for s in result if s["name"] == "www.example.com")
    assert len(www_entry["ips"]) == 2
    assert "amass,sublist3r" in www_entry["source"]

def test_save_and_load_list(tmp_path):
    items = ["www.example.com", "mail.example.com", "ftp.example.com"]
    filepath = tmp_path / "test_list.txt"

    save_list_to_file(items, filepath)
    assert filepath.exists()

    loaded = load_list_from_file(filepath)
    assert loaded == items

def test_extract_ips_from_results():
    results = {
        "hosts": [
            {"ip": "1.1.1.1", "ports": [{"port": 80}]},
            {"ip": "2.2.2.2", "ports": [{"port": 443}]}
        ]
    }

    ips = extract_ips_from_results(results)
    assert set(ips) == {"1.1.1.1", "2.2.2.2"}
