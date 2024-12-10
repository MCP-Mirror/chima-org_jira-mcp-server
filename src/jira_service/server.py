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
    CallToolResult,
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
TOOLS = ["jira_list_projects", "jira_get_project_details"]


async def fetch_jira_projects(number: int = 10) -> list[dict]:
    jira = JIRA(
        server=JIRA_SERVER,
        basic_auth=(JIRA_USER, API_KEY),
    )

    projects = []
    project_results = jira.projects()[:number]
    for project in project_results:
        projects.append({"id": project.id, "key": project.key, "name": project.name})

    return projects


async def fetch_jira_project_details(project_id: str) -> dict[str, Any]:
    jira = JIRA(
        server=JIRA_SERVER,
        basic_auth=(JIRA_USER, API_KEY),
    )

    return jira.project(project_id).raw


server = Server("jira-service")


# @server.list_resources()
# async def handle_list_resources() -> list[Resource]:
#     return [
#         Resource(
#             uri=AnyUrl(f"jira://internal/{project.key}"),
#             name=project.name,
#             description=f"Jira project {project.name}",
#         )
#         for project in jira.projects()
#     ]


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
                        "minimum": 1,
                        "maximum": 100,
                        "default": 10,
                    },
                },
            },
        ),
        Tool(
            name="jira_get_project_details",
            description="Get details of a Jira project",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "The ID of the Jira project",
                    },
                    "required": ["project_id"],
                },
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> CallToolResult:
    if name == "jira_list_projects":
        # Set default number of projects to list to 10
        number = int(arguments.get("number", 10))

        try:
            # Fetch projects from Jira
            projects = await fetch_jira_projects(number)

            # Return projects as a JSON string
            return CallToolResult(
                content=[TextContent(type="text", text=json.dumps(projects, indent=2))]
            )
        except Exception as e:
            logger.error(f"Error listing projects: {e}")
            return CallToolResult   (
                isError=True,
                content=[
                    TextContent(type="text", text=f"Error listing projects: {e}")
                ],
            )
    elif name == "jira_get_project_details":
        # Get project ID from arguments
        project_id = arguments.get("project_id")
        if not project_id:
            raise ValueError("project_id is required")

        try:
            # Fetch project details from Jira
            project = await fetch_jira_project_details(project_id)

            # Return project details as a JSON string
            return CallToolResult(
                content=[TextContent(type="text", text=json.dumps(project, indent=2))],
            )
        except Exception as e:
            logger.error(f"Error getting project details: {e}")
            return CallToolResult(
                isError=True,
                content=[
                    TextContent(type="text", text=f"Error getting project details: {e}")
                ],
            )
    else:
        raise ValueError(f"Unknown tool: {name}")


async def main():
    from mcp.server.stdio import stdio_server

    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream, write_stream, server.create_initialization_options()
        )
