"""Web crawler for detecting input fields and forms"""
from typing import Dict, Any, List
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time

class WebCrawlerProcessor:
    """Processor for crawling websites and detecting input fields"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Security Scanner) AppleWebKit/537.36'
        })

    def execute(self, task, previous_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute web crawling task

        Args:
            task: WorkflowTask with parameters:
                - source_task: Task ID containing URLs/subdomains
                - source_field: Field containing URLs
                - max_depth: Maximum crawl depth (default: 2)
                - max_pages: Maximum pages per domain (default: 50)
                - timeout: Request timeout in seconds (default: 10)
            previous_results: Previous task results

        Returns:
            Dictionary with pages_with_inputs list
        """
        try:
            params = task.parameters

            # Get source URLs
            source_task = params.get("source_task")
            source_field = params.get("source_field", "urls")

            if source_task not in previous_results:
                return {"success": False, "error": "Source task not found"}

            source_data = previous_results[source_task].get(source_field, [])

            # Ensure URLs have scheme
            urls = []
            for item in source_data:
                if isinstance(item, dict):
                    url = item.get("url") or f"https://{item.get('name', '')}"
                else:
                    url = item if item.startswith('http') else f"https://{item}"
                urls.append(url)

            # Crawl configuration
            max_depth = params.get("max_depth", 2)
            max_pages = params.get("max_pages", 50)
            timeout = params.get("timeout", 10)

            # Crawl each URL
            pages_with_inputs = []

            for base_url in urls:
                try:
                    crawled = self._crawl_site(
                        base_url,
                        max_depth=max_depth,
                        max_pages=max_pages,
                        timeout=timeout
                    )
                    pages_with_inputs.extend(crawled)
                except Exception as e:
                    continue  # Skip failed domains

            return {
                "success": True,
                "pages_with_inputs": pages_with_inputs,
                "total_pages": len(pages_with_inputs)
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _crawl_site(self, base_url: str, max_depth: int, max_pages: int, timeout: int) -> List[Dict]:
        """Crawl a single site and find forms with text inputs"""
        visited = set()
        to_visit = [(base_url, 0)]  # (url, depth)
        pages_with_inputs = []

        base_domain = urlparse(base_url).netloc

        while to_visit and len(visited) < max_pages:
            url, depth = to_visit.pop(0)

            if url in visited or depth > max_depth:
                continue

            visited.add(url)

            try:
                # Fetch page
                response = self.session.get(url, timeout=timeout, verify=False, allow_redirects=True)

                if response.status_code != 200:
                    continue

                # Parse HTML
                forms = self._parse_forms_from_html(response.text, url)

                # Filter forms with text inputs
                text_input_forms = self._filter_text_input_forms(forms)

                if text_input_forms:
                    pages_with_inputs.append({
                        "url": url,
                        "forms": text_input_forms
                    })

                # Extract links for further crawling
                if depth < max_depth:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    for link in soup.find_all('a', href=True):
                        next_url = urljoin(url, link['href'])
                        next_domain = urlparse(next_url).netloc

                        # Stay within same domain
                        if next_domain == base_domain and next_url not in visited:
                            to_visit.append((next_url, depth + 1))

                time.sleep(0.5)  # Rate limiting

            except Exception:
                continue

        return pages_with_inputs

    def _parse_forms_from_html(self, html: str, base_url: str) -> List[Dict]:
        """Parse forms from HTML"""
        soup = BeautifulSoup(html, 'html.parser')
        forms = []

        for form in soup.find_all('form'):
            action = form.get('action', '')
            method = form.get('method', 'get').lower()

            # Resolve relative URLs
            full_action = urljoin(base_url, action)

            # Extract inputs
            inputs = []
            for input_tag in form.find_all(['input', 'textarea']):
                input_type = input_tag.get('type', 'text')
                input_name = input_tag.get('name', '')

                inputs.append({
                    "type": input_type,
                    "name": input_name,
                    "value": input_tag.get('value', '')
                })

            forms.append({
                "action": full_action,
                "method": method,
                "inputs": inputs
            })

        return forms

    def _filter_text_input_forms(self, forms: List[Dict]) -> List[Dict]:
        """Filter forms that have text/password inputs"""
        text_types = {'text', 'password', 'email', 'search', 'tel', 'url'}

        filtered = []
        for form in forms:
            has_text_input = any(
                inp.get('type') in text_types or inp.get('type') == 'textarea'
                for inp in form.get('inputs', [])
            )
            if has_text_input:
                filtered.append(form)

        return filtered
