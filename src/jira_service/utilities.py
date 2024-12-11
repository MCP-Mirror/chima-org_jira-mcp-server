import asyncio
import json
import os
from typing import Any
from jira import JIRA
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API configuration
PERSONAL_JIRA_SERVER = "https://eddieho.atlassian.net"
PERSONAL_JIRA_USER = "edwin.ho.bj@gmail.com"
PERSONAL_JIRA_API_KEY = os.getenv("PERSONAL_JIRA_API_KEY")
if not PERSONAL_JIRA_API_KEY:
    raise ValueError("PERSONAL_JIRA_API_KEY environment variable required")

WORK_JIRA_SERVER = "https://withchima.atlassian.net"
WORK_JIRA_USER = "eddie@withchima.com"
WORK_JIRA_API_KEY = os.getenv("WORK_JIRA_API_KEY")
if not WORK_JIRA_API_KEY:
    raise ValueError("WORK_JIRA_API_KEY environment variable required")

# ============================
# Jira project utilities
# ============================


async def fetch_jira_projects() -> list[dict]:
    """
    Fetch a list of Jira projects.
    """
    jira = JIRA(
        server=WORK_JIRA_SERVER,
        basic_auth=(WORK_JIRA_USER, WORK_JIRA_API_KEY),
    )

    projects = []
    project_results = jira.projects()
    for project in project_results:
        projects.append({"id": project.id, "key": project.key, "name": project.name})

    return projects


async def fetch_jira_project_details(project_id: str) -> dict[str, Any]:
    """
    Fetch details of a specific Jira project.
    """
    jira = JIRA(
        server=WORK_JIRA_SERVER,
        basic_auth=(WORK_JIRA_USER, WORK_JIRA_API_KEY),
    )

    return jira.project(project_id).raw


# ============================
# Jira issue utilities
# ============================


async def search_jira_issues(
    issue_id: str, project_id: str, number: int = 10, cursor: int = 0
) -> list[dict]:
    """
    Fetch a list of Jira issues for a specific project.
    """
    jira = JIRA(
        server=WORK_JIRA_SERVER,
        basic_auth=(WORK_JIRA_USER, WORK_JIRA_API_KEY),
    )

    # Build the query
    query = ""
    if project_id:
        query += f"project = {project_id}"
    if issue_id:
        if query:
            query += " AND "
        query += f"issue = {issue_id}"
    if not query:
        raise ValueError("Either project_id or issue_id must be provided")

    # Search for issues
    issues = jira.search_issues(
        query,
        maxResults=number,
        startAt=cursor,
        json_result=True,
        fields="id,key,summary,assignee,reporter",
    )

    return issues.get("issues")


async def add_jira_issue_comment(issue_id: str, comment: str) -> dict:
    """
    Add a comment to a Jira issue.
    """
    jira = JIRA(
        server=PERSONAL_JIRA_SERVER,
        basic_auth=(PERSONAL_JIRA_USER, PERSONAL_JIRA_API_KEY),
    )

    # Add comment to issue
    comment_id = jira.add_comment(issue_id, comment)

    return {"comment_id": comment_id}


# if __name__ == "__main__":

#     async def main():
#         issues = await add_jira_issue_comment("BTS-1", "This is a test comment")
#         print(issues)

#     asyncio.run(main())
