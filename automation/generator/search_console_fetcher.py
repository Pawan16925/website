"""Fetch StaxTech Search Console queries for topic discovery.

Authentication:
- GSC_SERVICE_ACCOUNT_JSON: GitHub Actions secret containing the service-account
  JSON object.
- GSC_SITE_URL: Search Console property, e.g. https://www.staxtech.in/
The service account must be granted access to the Search Console property.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from google.oauth2 import service_account
from googleapiclient.discovery import build


ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "automation" / "data" / "search-console-candidates.json"
SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]


def main() -> int:
    raw_credentials = os.getenv("GSC_SERVICE_ACCOUNT_JSON", "").strip()
    site_url = os.getenv("GSC_SITE_URL", "https://www.staxtech.in/").strip()

    if not raw_credentials:
        print(
            "GSC credentials are not configured; Search Console enrichment skipped."
        )
        return 0

    try:
        credentials_info = json.loads(raw_credentials)
        credentials = service_account.Credentials.from_service_account_info(
            credentials_info, scopes=SCOPES
        )
        service = build(
            "searchconsole",
            "v1",
            credentials=credentials,
            cache_discovery=False,
        )

        # Search Console data can lag, so query a completed recent window.
        end_date = datetime.now(timezone.utc).date() - timedelta(days=2)
        start_date = end_date - timedelta(days=28)

        response = (
            service.searchanalytics()
            .query(
                siteUrl=site_url,
                body={
                    "startDate": start_date.isoformat(),
                    "endDate": end_date.isoformat(),
                    "dimensions": ["query"],
                    "dimensionFilterGroups": [{
                        "groupType": "and",
                        "filters": [{
                            "dimension": "country",
                            "operator": "equals",
                            "expression": "USA"
                        }]
                    }],
                    "rowLimit": 250,
                    "dataState": "final",
                },
            )
            .execute()
        )

        rows = response.get("rows", [])
        topics = []
        for row in rows:
            query = str(row.get("keys", [""])[0]).strip()
            if not query:
                continue
            topics.append(
                {
                    "title": query,
                    "source": "Google Search Console",
                    "source_url": site_url,
                    "geo": "US",
                    "clicks": row.get("clicks", 0),
                    "impressions": row.get("impressions", 0),
                    "ctr": row.get("ctr", 0),
                    "position": row.get("position", 0),
                }
            )

        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT.write_text(
            json.dumps(
                {
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "count": len(topics),
                    "topics": topics,
                },
                indent=2,
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )
        print(f"Saved {len(topics)} Search Console queries.")
        return 0

    except Exception as exc:
        print(f"Search Console enrichment failed: {exc}", file=sys.stderr)
        # Do not break the primary Google Trends publishing pipeline.
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
