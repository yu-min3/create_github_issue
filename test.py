import json
import os
import requests
from datetime import datetime

GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
REPO_OWNER = os.environ["REPO_OWNER"]  # e.g. your-org-name
REPO_NAME = os.environ["REPO_NAME"]    # e.g. alert-tracker

def create_issue(app_name,alert_level,message, context):

    timestamp = datetime.utcnow().isoformat() + "Z"

    issue_title = f"[{alert_level}] Alert from {app_name}"
    issue_body = f"""
        ## アラート情報

        - **アプリ名**: {app_name}
        - **アラートレベル**: {alert_level}
        - **発生時刻 (UTC)**: {timestamp}

        ---

        ### メッセージ内容:{message}
        """

    labels = [app_name, alert_level, "未対応"]

    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }

    issue_data = {
        "title": issue_title,
        "body": issue_body,
        "labels": labels
    }

    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/issues"

    response = requests.post(url, headers=headers, json=issue_data)
    print("GitHub Response:", response.status_code, response.text)

    if response.status_code >= 300:
        raise Exception("Issue creation failed")

    return {
        "statusCode": 200,
        "body": json.dumps("Issue created successfully")
    }