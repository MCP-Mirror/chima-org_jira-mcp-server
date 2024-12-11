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
    LoggingLevel,
)
from pydantic import AnyUrl

from .utilities import (
    fetch_jira_projects,
    fetch_jira_project_details,
    search_jira_issues,
    add_jira_issue_comment,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("jira-server")


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
    """
    List all Jira tools
    """
    return [
        Tool(
            name="jira_list_projects",
            description="List all Jira projects",
            inputSchema={
                "type": "object",
                "properties": {},
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
        Tool(
            name="jira_search_issues",
            description="Search for Jira issues",
            inputSchema={
                "type": "object",
                "properties": {
                    "issue_id": {
                        "type": "string",
                        "description": "The ID of the Jira issue",
                    },
                    "project_id": {
                        "type": "string",
                        "description": "The ID of the Jira project",
                    },
                    "number": {
                        "type": "number",
                        "description": "Maximum number of issues to list (default 10)",
                        "minimum": 1,
                        "maximum": 50,
                        "default": 10,
                    },
                    "cursor": {
                        "type": "number",
                        "description": "The cursor to start from (default 0)",
                        "minimum": 0,
                        "default": 0,
                    },
                },
            },
        ),
        Tool(
            name="jira_add_issue_comment",
            description="Add a comment to a Jira issue",
            inputSchema={
                "type": "object",
                "properties": {
                    "issue_id": {
                        "type": "string",
                        "description": "The ID of the Jira issue",
                    },
                    "comment": {
                        "type": "string",
                        "description": "The comment to add to the Jira issue",
                    },
                },
                "required": ["issue_id", "comment"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> CallToolResult:
    """
    Call a Jira tool
    """
    if name == "jira_list_projects":
        try:
            # Fetch projects from Jira
            projects = await fetch_jira_projects()

            # Return projects as a JSON string
            return [TextContent(type="text", text=json.dumps(projects, indent=2))]
        except Exception as e:
            logger.error(f"Error listing projects: {e}")
            return CallToolResult(
                isError=True,
                content=[TextContent(type="text", text=f"Error listing projects: {e}")],
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
            return [TextContent(type="text", text=json.dumps(project, indent=2))]
        except Exception as e:
            logger.error(f"Error getting project details: {e}")
            return CallToolResult(
                isError=True,
                content=[
                    TextContent(type="text", text=f"Error getting project details: {e}")
                ],
            )
    elif name == "jira_search_issues":
        # Get issue ID abd project ID from arguments
        issue_id = arguments.get("issue_id")
        project_id = arguments.get("project_id")
        if not issue_id and not project_id:
            raise ValueError("Either issue_id or project_id is required")

        # Set default number of issues to list to 10
        number = int(arguments.get("number", 10))
        # Set default cursor to 0
        cursor = int(arguments.get("cursor", 0))

        try:
            # Fetch issues from Jira
            issues = await search_jira_issues(issue_id, project_id, number, cursor)

            # Return issues as a JSON string
            return [TextContent(type="text", text=json.dumps(issues, indent=2))]
        except Exception as e:
            logger.error(f"Error searching issues: {e}")
            return CallToolResult(
                isError=True,
                content=[TextContent(type="text", text=f"Error searching issues: {e}")],
            )
    elif name == "jira_add_issue_comment":
        # Get issue ID and comment from arguments
        issue_id = arguments.get("issue_id")
        comment = arguments.get("comment")
        if not issue_id or not comment:
            raise ValueError("issue_id and comment are required")

        try:
            # Add comment to Jira issue
            await add_jira_issue_comment(issue_id, comment)
            return [TextContent(type="text", text="Comment added successfully")]
        except Exception as e:
            logger.error(f"Error adding comment to issue: {e}")
            return CallToolResult(
                isError=True,
                content=[
                    TextContent(type="text", text=f"Error adding comment to issue: {e}")
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
