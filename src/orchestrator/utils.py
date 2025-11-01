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
from typing import TypeVar

from pydantic import BaseModel
from pydantic import ValidationError

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


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
                f"Command failed with code {result.returncode}: {' '.join(command)}\nstderr: {result.stderr}"
            )

        return result

    except subprocess.TimeoutExpired:
        logger.error(f"Command timed out after {timeout}s: {' '.join(command)}")
        raise

    except FileNotFoundError:
        logger.error(f"Command not found: {command[0]}")
        raise

    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed with code {e.returncode}: {' '.join(command)}\nstderr: {e.stderr}")
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


def build_agent_prompt(
    agent_name: str,
    task: str,
    data: dict,
    schema: type[BaseModel],
) -> str:
    """Build agent prompt with explicit JSON schema requirements.

    Creates structured prompt that:
    - Clearly separates instructions from data
    - Includes JSON schema from Pydantic model
    - Provides example output format
    - Uses delimiters to prevent context contamination

    Args:
        agent_name: Name of agent being invoked
        task: High-level task description
        data: Data to analyze (will be JSON serialized)
        schema: Pydantic model class defining expected response structure

    Returns:
        Formatted prompt string with JSON requirements

    Example:
        >>> prompt = build_agent_prompt(
        ...     "analysis-expert",
        ...     "Analyze ticket validity",
        ...     {"ticket": {...}},
        ...     ValidityAnalysis
        ... )
    """
    # Get JSON schema from Pydantic model
    schema_dict = schema.model_json_schema()

    # Build structured prompt with clear delimiters
    prompt = f"""You are {agent_name}. Your task: {task}

IMPORTANT: Return ONLY valid JSON matching this exact schema. No explanatory text, no markdown wrapping.

Required JSON Schema:
{json.dumps(schema_dict, indent=2)}

Example format:
{json.dumps(schema.model_json_schema()["properties"], indent=2)}

===== DATA TO ANALYZE =====
{json.dumps(data, indent=2)}
===== END DATA =====

Return your analysis as valid JSON only."""

    return prompt


def call_agent_with_retry(
    agent_name: str,
    task: str,
    data: dict,
    schema: type[T],
    max_retries: int = 3,
    timeout: int = 60,
) -> T:
    """Call agent with automatic retry on malformed responses.

    Implements defensive pattern from DISCOVERIES.md lines 200-270:
    - Builds structured prompts requesting JSON
    - Parses responses defensively with parse_llm_json()
    - Retries with error feedback if parsing fails
    - Validates with Pydantic schema

    Args:
        agent_name: Name of agent to invoke (e.g., "analysis-expert")
        task: High-level task description
        data: Data for agent to analyze
        schema: Pydantic model defining expected response structure
        max_retries: Maximum retry attempts (default: 3)
        timeout: Timeout per agent call in seconds (default: 60)

    Returns:
        Validated Pydantic model instance

    Raises:
        ValueError: If all retries fail to produce valid JSON
        ValidationError: If JSON doesn't match Pydantic schema

    Example:
        >>> validity = call_agent_with_retry(
        ...     agent_name="analysis-expert",
        ...     task="Analyze ticket validity",
        ...     data={"ticket": ticket_data},
        ...     schema=ValidityAnalysis
        ... )
    """
    last_error = None

    for attempt in range(max_retries):
        try:
            # Build prompt with JSON requirements
            if attempt == 0:
                prompt = build_agent_prompt(agent_name, task, data, schema)
            else:
                # On retry, include feedback about previous error
                prompt = f"""Previous attempt failed with error: {last_error}

Please try again, ensuring you return ONLY valid JSON with no additional text.

{build_agent_prompt(agent_name, task, data, schema)}"""

            logger.debug(f"Agent call attempt {attempt + 1}/{max_retries} for {agent_name}")

            # Call agent
            response = run_agent(agent_name, prompt, timeout=timeout)

            # Parse JSON defensively
            try:
                json_data = parse_llm_json(response)
            except ValueError as e:
                last_error = str(e)
                logger.warning(f"Attempt {attempt + 1} failed to parse JSON: {last_error}")
                if attempt < max_retries - 1:
                    continue
                raise

            # Validate with Pydantic schema
            try:
                return schema(**json_data)
            except ValidationError as e:
                last_error = f"Schema validation failed: {e}"
                logger.warning(f"Attempt {attempt + 1} failed validation: {last_error}")
                if attempt < max_retries - 1:
                    continue
                raise

        except Exception as e:
            last_error = str(e)
            logger.warning(f"Attempt {attempt + 1} failed: {last_error}")
            if attempt < max_retries - 1:
                continue
            raise

    # Should never reach here due to raise in loop, but for type safety
    raise ValueError(f"All {max_retries} attempts failed. Last error: {last_error}")
