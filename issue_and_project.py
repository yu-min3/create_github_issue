import os
import requests
import json
from datetime import datetime

GITHUB_TOKEN = os.environ["PROJECT_GITHUB_TOKEN"]
REPO_OWNER = os.environ["REPO_OWNER"]
REPO_NAME = os.environ["REPO_NAME"]
PROJECT_NUMBER = int(os.environ["PROJECT_NUMBER"])

headers = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"
}


def create_issue(title, body, labels):
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/issues"
    payload = {
        "title": title,
        "body": body,
        "labels": labels
    }
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()


def get_project_id():
    query = """
    query($owner: String!, $number: Int!) {
      user(login: $owner) {
        projectV2(number: $number) {
          id
        }
      }
    }
    """
    variables = {"owner": REPO_OWNER, "number": PROJECT_NUMBER}
    res = requests.post("https://api.github.com/graphql", headers=headers, json={
        "query": query, "variables": variables
    })
    res.raise_for_status()
    data = res.json()
    print("Project fetch response:", json.dumps(data, indent=2))

    return data["data"]["user"]["projectV2"]["id"]


def get_issue_node_id(issue_number):
    query = """
    query($owner: String!, $repo: String!, $issue: Int!) {
      repository(owner: $owner, name: $repo) {
        issue(number: $issue) {
          id
        }
      }
    }
    """
    variables = {
        "owner": REPO_OWNER,
        "repo": REPO_NAME,
        "issue": issue_number
    }
    res = requests.post("https://api.github.com/graphql", headers=headers, json={
        "query": query, "variables": variables
    })
    res.raise_for_status()
    return res.json()["data"]["repository"]["issue"]["id"]


def add_issue_to_project_and_get_item_id(project_id, issue_node_id):
    mutation = """
    mutation($projectId: ID!, $contentId: ID!) {
      addProjectV2ItemById(input: {projectId: $projectId, contentId: $contentId}) {
        item {
          id
        }
      }
    }
    """
    variables = {
        "projectId": project_id,
        "contentId": issue_node_id
    }
    res = requests.post("https://api.github.com/graphql", headers=headers, json={
        "query": mutation, "variables": variables
    })
    res.raise_for_status()
    return res.json()["data"]["addProjectV2ItemById"]["item"]["id"]


def get_project_field_ids(project_id):
    query = """
    query($projectId: ID!) {
      node(id: $projectId) {
        ... on ProjectV2 {
          fields(first: 20) {
            nodes {
              ... on ProjectV2FieldCommon {
                id
                name
                dataType
              }
              # 他の型がある場合はここに追加可能
            }
          }
        }
      }
    }
    """
    res = requests.post("https://api.github.com/graphql", headers=headers, json={
        "query": query,
        "variables": {"projectId": project_id}
    })
    res.raise_for_status()

    result = res.json()
    print("📦 get_project_field_ids response:", json.dumps(result, indent=2))

    return {field["name"]: field["id"] for field in result["data"]["node"]["fields"]["nodes"]}



def set_project_field_value_text(project_id, item_id, field_id, value):
    mutation = """
    mutation($input: UpdateProjectV2ItemFieldValueInput!) {
      updateProjectV2ItemFieldValue(input: $input) {
        projectV2Item {
          id
        }
      }
    }
    """
    variables = {
        "input": {
            "projectId": project_id,
            "itemId": item_id,
            "fieldId": field_id,
            "value": {
                "text": value
            }
        }
    }
    res = requests.post("https://api.github.com/graphql", headers=headers, json={
        "query": mutation, "variables": variables
    })
    res.raise_for_status()
    return res.json()


# ========================
# 実行例（アラート情報）
# ========================

app_name = "MyApp1"
alert_level = "High"
message = "CPU使用率が90%を超えました"
timestamp = datetime.utcnow().isoformat() + "Z"

issue = create_issue(
    title=f"[{alert_level}] {app_name} Alert",
    body=f"""
## アラート情報

- **アプリ名**: {app_name}
- **アラートレベル**: {alert_level}
- **発生時刻 (UTC)**: {timestamp}

---

### メッセージ内容:{message}
""",
    labels=[app_name, alert_level, "未対応"]
)

issue_number = issue["number"]
issue_node_id = get_issue_node_id(issue_number)
project_id = get_project_id()
item_id = add_issue_to_project_and_get_item_id(project_id, issue_node_id)
field_ids = get_project_field_ids(project_id)

# カスタムフィールドに値をセット
set_project_field_value_text(
    project_id, item_id, field_ids["alert_level"], alert_level)
set_project_field_value_text(
    project_id, item_id, field_ids["app_name"], app_name)

print("✅ 完了：Issue作成 + Projects追加 + カスタムフィールド設定")