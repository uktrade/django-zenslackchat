import requests
from requests.auth import HTTPBasicAuth
from bs4 import BeautifulSoup
from datetime import datetime
import os
import sys
import logging
from django.conf import settings

log = logging.getLogger(__name__)

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'webapp.settings')


def get_oncall_support(content):
    """Extract today's Primary and Secondary on-call support from an HTML table."""
    soup = BeautifulSoup(content, "html.parser")

    today = datetime.today()
    today = today.replace(hour=0, minute=0, second=0, microsecond=0)
    primary, secondary = None, None

    # Loop through table rows
    for row in soup.find_all("tr"):
        cols = row.find_all("td")
        if len(cols) >= 5:  # Ensure it has necessary columns
            date_range = cols[0].get_text(strip=True)

            try:
                # Extract start and end dates
                start_date_str, end_date_str = date_range.split(" - ")
                start_date = datetime.strptime(start_date_str, "%d/%m/%y")
                end_date = datetime.strptime(end_date_str, "%d/%m/%y")

                # Check if today falls within the date range
                if start_date <= today <= end_date:
                    primary = cols[1].get_text(strip=True)
                    secondary = cols[3].get_text(strip=True)
                    break  # Stop once today's entry is found

            except ValueError:
                continue  # Skip invalid date formats

    return primary, secondary


def call_atlassian():
    # API Endpoint
    url = f"{settings.ATLASSIAN_BASE_URL}/rest/api/content/{settings.ATLASSIAN_PAGE_ID}?expand=body.storage"

    # Request headers
    headers = {
        "Accept": "application/json"
    }
    log.debug("atlassian login")
    # Make the request
    response = requests.get(
                url,
                headers=headers,
                auth=HTTPBasicAuth(settings.ATLASSIAN_USERNAME, settings.ATLASSIAN_API_TOKEN)
            )

    # Parse response
    if response.status_code == 200:
        data = response.json()
        content = data["body"]["storage"]["value"]  # HTML format
    else:
        print(f"Error: {response.status_code} - {response.text}")

    primary, secondary = get_oncall_support(content)
    log.debug(f"{primary} {secondary}")

    # print(f"Primary: {primary}")
    # print(f"Secondary: {secondary}")
    oncall = {"primary": primary, "secondary": secondary}
    log.debug(f"{oncall}")
    return oncall

# oncall = call_atlassian()
# print(oncall)
