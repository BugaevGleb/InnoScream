import json
import logging
import urllib.parse
from typing import List, Dict

logger = logging.getLogger(__name__)

BASE_URL = "https://quickchart.io/chart"

def generate_weekly_stress_chart_url(daily_stats: List[Dict[str, int]]) -> str:
    """Generates a QuickChart URL for the weekly stress bar chart.

    Args:
        daily_stats: A list of dictionaries, e.g., 
                     [{'day': 'Mon', 'count': 10}, {'day': 'Tue', 'count': 5}, ...]
                     Expected to contain 7 entries, one for each day Mon-Sun.

    Returns:
        The QuickChart URL string.
    """
    # Ensure the order is Mon, Tue, ..., Sun
    days_order = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    stats_dict = {item['day']: item['count'] for item in daily_stats}
    
    labels = days_order
    data = [stats_dict.get(day, 0) for day in days_order] # Ensure correct order and handle missing days

    chart_config = {
        "type": "bar",
        "data": {
            "labels": labels,
            "datasets": [{
                "label": "Screams per Day",
                "data": data,
                "backgroundColor": "rgba(54, 162, 235, 0.6)", # Blue color
                "borderColor": "rgba(54, 162, 235, 1)",
                "borderWidth": 1
            }]
        },
        "options": {
            "title": {
                "display": True,
                "text": "Weekly Stress Levels (Screams per Day)"
            },
            "scales": {
                "yAxes": [{
                    "ticks": {
                        "beginAtZero": True,
                        "stepSize": 1 # Ensure integer steps for counts
                    }
                }]
            },
            "legend": {
                "display": False # Hide legend as there's only one dataset
            }
        }
    }

    # Convert config to JSON string and URL-encode it
    chart_json = json.dumps(chart_config)
    encoded_chart_json = urllib.parse.quote(chart_json)

    # Construct the final URL
    # Optional: Add width/height parameters: &w=600&h=400
    chart_url = f"{BASE_URL}?c={encoded_chart_json}" 
    
    logger.info(f"Generated QuickChart URL: {chart_url}")
    return chart_url

# Example usage (for testing)
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    example_stats = [
        {'day': 'Mon', 'count': 12},
        {'day': 'Tue', 'count': 19},
        {'day': 'Wed', 'count': 3},
        {'day': 'Thu', 'count': 5},
        {'day': 'Fri', 'count': 2},
        {'day': 'Sat', 'count': 3},
        {'day': 'Sun', 'count': 8}
    ]
    url = generate_weekly_stress_chart_url(example_stats)
    print(f"Example Chart URL: {url}")

    # Example with missing data
    example_stats_missing = [
        {'day': 'Mon', 'count': 12},
        {'day': 'Wed', 'count': 3},
        {'day': 'Fri', 'count': 2},
    ]
    url_missing = generate_weekly_stress_chart_url(example_stats_missing)
    print(f"Example Chart URL (missing data): {url_missing}") 