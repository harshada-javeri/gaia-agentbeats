#!/usr/bin/env python3
"""Generate docker-compose.yml from scenario.toml for AgentBeats assessment."""

import argparse
import json
import sys
import tomllib
from pathlib import Path
from typing import Any, Dict, List

import requests


def get_agent_image(agentbeats_id: str, agent_type: str) -> str:
    """Get the container image URL for an AgentBeats agent."""
    try:
        # Query AgentBeats API for agent details
        response = requests.get(f"https://api.agentbeats.dev/agents/{agentbeats_id}", timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get("image_uri", "")
    except Exception as e:
        print(f"Warning: Could not fetch agent image from AgentBeats: {e}", file=sys.stderr)
    
    return ""


def load_scenario(scenario_path: str) -> Dict[str, Any]:
    """Load scenario.toml file."""
    try:
        with open(scenario_path, "rb") as f:
            return tomllib.load(f)
    except FileNotFoundError:
        print(f"Error: scenario.toml not found at {scenario_path}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error reading scenario.toml: {e}", file=sys.stderr)
        sys.exit(1)


def resolve_image(agent_spec: Dict[str, Any]) -> str:
    """Resolve image URI from agent specification."""
    # Prefer explicit image over agentbeats_id
    if "image" in agent_spec:
        return agent_spec["image"]
    
    if "agentbeats_id" in agent_spec and agent_spec["agentbeats_id"]:
        agent_type = "green" if "green" in str(agent_spec) else "purple"
        image = get_agent_image(agent_spec["agentbeats_id"], agent_type)
        if image:
            return image
        
        # Fall back to a placeholder if we can't resolve
        agent_id = agent_spec["agentbeats_id"]
        return f"ghcr.io/agentbeats/{agent_id}:latest"
    
    print(f"Error: No image specified for agent: {agent_spec}", file=sys.stderr)
    sys.exit(1)


def resolve_env(env_dict: Dict[str, str]) -> Dict[str, str]:
    """Resolve environment variables (handle ${VAR} syntax)."""
    import os
    
    resolved = {}
    for key, value in env_dict.items():
        if value.startswith("${") and value.endswith("}"):
            # This is a reference to an environment variable
            var_name = value[2:-1]
            resolved[key] = os.environ.get(var_name, "")
        else:
            resolved[key] = value
    
    return resolved


def build_docker_compose(scenario: Dict[str, Any]) -> Dict[str, Any]:
    """Build docker-compose configuration from scenario."""
    green_agent = scenario.get("green_agent", {})
    participants = scenario.get("participants", [])
    config = scenario.get("config", {})
    
    services = {}
    
    # Green agent service
    green_image = resolve_image(green_agent)
    green_env = resolve_env(green_agent.get("env", {}))
    
    services["green_agent"] = {
        "image": green_image,
        "ports": ["9001:9001"],
        "environment": {
            **green_env,
            "HOST": "0.0.0.0",
            "PORT": "9001",
        },
        "command": ["--host", "0.0.0.0", "--port", "9001"],
    }
    
    # Participant services
    for i, participant in enumerate(participants):
        service_name = participant.get("name", f"participant_{i}")
        participant_image = resolve_image(participant)
        participant_env = resolve_env(participant.get("env", {}))
        port = 9002 + i
        
        services[service_name] = {
            "image": participant_image,
            "ports": [f"{port}:{port}"],
            "environment": {
                **participant_env,
                "HOST": "0.0.0.0",
                "PORT": str(port),
            },
            "command": ["--host", "0.0.0.0", "--port", str(port)],
        }
    
    return {
        "version": "3.8",
        "services": services,
        "networks": {
            "default": {"driver": "bridge"}
        },
    }


def write_docker_compose(compose_config: Dict[str, Any], output_path: str = "docker-compose.yml"):
    """Write docker-compose configuration to file."""
    import yaml
    
    with open(output_path, "w") as f:
        yaml.dump(compose_config, f, default_flow_style=False, sort_keys=False)
    
    print(f"✅ Generated {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate docker-compose.yml from AgentBeats scenario.toml"
    )
    parser.add_argument(
        "--scenario",
        default="scenario.toml",
        help="Path to scenario.toml file",
    )
    parser.add_argument(
        "--output",
        "-o",
        default="docker-compose.yml",
        help="Output file for docker-compose.yml",
    )
    
    args = parser.parse_args()
    
    # Load scenario
    scenario = load_scenario(args.scenario)
    
    # Build docker-compose
    compose_config = build_docker_compose(scenario)
    
    # Write docker-compose.yml
    write_docker_compose(compose_config, args.output)
    
    # Also print the config for GitHub Actions to capture
    print("\n📋 Generated docker-compose.yml:")
    import yaml
    print(yaml.dump(compose_config, default_flow_style=False, sort_keys=False))


if __name__ == "__main__":
    main()
