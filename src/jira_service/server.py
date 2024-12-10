import os
import json
import logging
from datetime import datetime, timedelta
from collections.abc import Sequence
from functools import lru_cache
from typing import Any

import httpx
import asyncio
from dotenv import load_dotenv
from mcp.server import Server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
    LoggingLevel,
)
from pydantic import AnyUrl
from jira import JIRA

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("jira-server")

# API configuration
API_KEY = os.getenv("JIRA_API_KEY")
if not API_KEY:
    raise ValueError("JIRA_API_KEY environment variable required")

JIRA_SERVER = "https://eddieho.atlassian.net"
JIRA_USER = "edwin.ho.bj@gmail.com"

# Initialize Jira client
jira = JIRA(
    server=JIRA_SERVER,
    basic_auth=(JIRA_USER, API_KEY),
)

server = Server("jira-service")


@server.list_resources()
async def handle_list_resources() -> list[Resource]:
    return [
        Resource(
            uri=AnyUrl(f"jira://internal/{project.key}"),
            name=project.name,
            description=f"Jira project {project.name}",
        )
        for project in jira.projects()
    ]


@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    return [
        Tool(
            name="jira_list_projects",
            description="List all Jira projects",
            inputSchema={
                "type": "object",
                "properties": {
                    "number": {
                        "type": "number",
                        "description": "Maximum number of projects to list (default 10)",
                        "default": 10,
                    },
                },
            },
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> str:
    if name != "jira_list_projects":
        raise ValueError(f"Unknown tool: {name}")

    number = int(arguments.get("number", 10))

    try:
        projects = []
        project_results = jira.projects()[:number]
        for project in project_results:
            projects.append(
                {
                    "key": project.key,
                    "name": project.name,
                    "description": project.description,
                }
            )

        return [TextContent(type="text", text=json.dumps(projects, indent=2))]
    except Exception as e:
        logger.error(f"Error listing projects: {e}")
        raise RuntimeError(f"Error listing projects: {e}")
