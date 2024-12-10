import os
import json
from jira import JIRA
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API configuration
JIRA_API_KEY = os.getenv("JIRA_API_KEY")
if not JIRA_API_KEY:
    raise ValueError("JIRA_API_KEY environment variable required")

# Connect to Jira
JIRA_SERVER = "https://eddieho.atlassian.net"
JIRA_USER = "edwin.ho.bj@gmail.com"


def fetch_jira_projects(number: int = 10) -> list[dict]:
    jira = JIRA(
        server=JIRA_SERVER,
        basic_auth=(JIRA_USER, JIRA_API_KEY),
    )

    projects = []
    project_results = jira.projects()
    for project in project_results:
        projects.append({"id": project.id, "key": project.key, "name": project.name})

    return projects


jira = JIRA(
    server=JIRA_SERVER,
    basic_auth=(JIRA_USER, JIRA_API_KEY),
)

# Get all projects
projects = jira.projects()
print(projects)

demo_project = jira.project("BTS")
print(json.dumps(demo_project.raw, indent=2))
