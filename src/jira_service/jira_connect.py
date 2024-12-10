import os
from jira import JIRA
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API configuration
JIRA_API_KEY = os.getenv("JIRA_API_KEY")
if not JIRA_API_KEY:
    raise ValueError("JIRA_API_KEY environment variable required")

# Connect to Jira
jira = JIRA(
    server="https://eddieho.atlassian.net",
    basic_auth=("edwin.ho.bj@gmail.com", JIRA_API_KEY),
)
print("Connected to Jira")

# Get all projects
projects = jira.projects()
print(projects)

demo_project = jira.project("BTS")
print(demo_project)

