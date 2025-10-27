"""Defensive utilities for orchestrator workflows.

This module provides robust utilities for working with LLMs, CLI commands,
and Claude Code SDK agent delegation. All functions include comprehensive
error handling and logging.
"""

import json
import logging
import re
import subprocess
from typing import Any

logger = logging.getLogger(__name__)


def parse_llm_json(response: str) -> dict[str, Any]:
    """Extract JSON from LLM response with defensive parsing.

    Handles common LLM response formats:
    - Markdown-wrapped JSON (```json...```)
    - JSON with explanatory text before/after
    - Nested JSON objects
    - Malformed quotes and escaping

    Args:
        response: Raw LLM response text

    Returns:
        Parsed JSON as dictionary

    Raises:
        ValueError: If no valid JSON can be extracted
    """
    if not response or not response.strip():
        raise ValueError("Empty response from LLM")

    # Try direct JSON parse first (fastest path)
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        pass

    # Extract from markdown code blocks
    markdown_patterns = [
        r"```json\s*(.*?)\s*```",  # ```json ... ```
        r"```\s*(.*?)\s*```",  # ``` ... ```
    ]

    for pattern in markdown_patterns:
        matches = re.findall(pattern, response, re.DOTALL | re.IGNORECASE)
        for match in matches:
            try:
                return json.loads(match.strip())
            except json.JSONDecodeError:
                continue

    # Find JSON object boundaries - use non-greedy matching to avoid
    # capturing multiple objects with invalid text between them
    json_patterns = [
        r"\{(?:[^{}]|(?:\{[^{}]*\}))*\}",  # Nested objects (max 2 levels)
        r"\[(?:[^\[\]]|(?:\[[^\[\]]*\]))*\]",  # Nested arrays (max 2 levels)
    ]

    for pattern in json_patterns:
        matches = re.findall(pattern, response, re.DOTALL)
        # Try each match, longest first
        for match in sorted(matches, key=len, reverse=True):
            try:
                return json.loads(match)
            except json.JSONDecodeError:
                continue

    # If all parsing attempts fail, raise with helpful context
    preview = response[:200] + ("..." if len(response) > 200 else "")
    raise ValueError(f"Could not extract valid JSON from LLM response. Preview: {preview}")


def run_cli_command(
    command: list[str],
    timeout: int = 300,
    check: bool = True,
) -> subprocess.CompletedProcess:
    """Run CLI command with comprehensive error handling.

    Args:
        command: Command and arguments as list (e.g., ["gh", "issue", "view", "123"])
        timeout: Maximum execution time in seconds (default: 300)
        check: Raise CalledProcessError if command fails (default: True)

    Returns:
        CompletedProcess with stdout, stderr, and returncode

    Raises:
        subprocess.TimeoutExpired: If command exceeds timeout
        subprocess.CalledProcessError: If command fails and check=True
        FileNotFoundError: If command executable not found
    """
    logger.debug(f"Running command: {' '.join(command)}")

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=check,
        )

        if result.returncode == 0:
            logger.debug(f"Command succeeded: {' '.join(command)}")
        else:
            logger.warning(
                f"Command failed with code {result.returncode}: {' '.join(command)}\n"
                f"stderr: {result.stderr}"
            )

        return result

    except subprocess.TimeoutExpired:
        logger.error(f"Command timed out after {timeout}s: {' '.join(command)}")
        raise

    except FileNotFoundError:
        logger.error(f"Command not found: {command[0]}")
        raise

    except subprocess.CalledProcessError as e:
        logger.error(
            f"Command failed with code {e.returncode}: {' '.join(command)}\n"
            f"stderr: {e.stderr}"
        )
        raise


def run_agent(agent_name: str, task_description: str, timeout: int = 60) -> str:
    """Delegate task to Claude Code agent via --agents flag.

    Command format:
        claude --print --agents '{agent_name: {...}}' "prompt"

    Note: Using amplifier's existing agents would require them to be
    defined in .claude/agents/. For now, using --agents flag for
    dynamic agent creation.

    Args:
        agent_name: Name of agent to spawn (e.g., "analysis-expert", "bug-hunter")
        task_description: Task description/prompt for the agent
        timeout: Maximum execution time in seconds (default: 60)

    Returns:
        Agent's response as string

    Raises:
        subprocess.CalledProcessError: If agent execution fails
        subprocess.TimeoutExpired: If agent exceeds timeout
    """
    logger.info(f"Delegating to {agent_name}: {task_description[:100]}...")

    # Format agent definition
    agent_def = {
        agent_name: {
            "description": f"Specialized agent for {agent_name}",
            "prompt": task_description,
        }
    }

    command = [
        "claude",
        "--print",
        "--agents",
        json.dumps(agent_def),
        task_description,
    ]

    return run_cli_command(command, timeout=timeout).stdout
