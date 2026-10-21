"""One-time setup: create (or update) the Managed Agents environment and agent.

Run this before run.py, and again whenever agent_prompt.md or apps.json changes.
IDs are stored in .state.json so every run reuses the same agent and environment.
"""

import hashlib
import json
from pathlib import Path

import anthropic

HERE = Path(__file__).parent
STATE_FILE = HERE / ".state.json"

ENV_NAME = "oauth-capture-experiment"
AGENT_NAME = "OAuth setup recorder (experiment)"
MODEL = {"id": "claude-opus-5-5", "effort": "high"}


def load_apps():
    return json.loads((HERE / "apps.json").read_text())


def environment_config(apps):
    hosts = sorted({h for app in apps for h in app["allowed_hosts"]})
    return {
        "type": "cloud",
        # Only the providers' own hosts. Playwright and Chromium are preinstalled,
        # so no package registries are needed.
        "networking": {"type": "limited", "allowed_hosts": hosts},
    }


def agent_fields():
    return {
        "name": AGENT_NAME,
        "model": MODEL,
        "system": (HERE / "agent_prompt.md").read_text(),
        "tools": [
            {
                "type": "agent_toolset_20260401",
                "default_config": {"enabled": True, "permission_policy": {"type": "auto"}},
                "configs": [
                    # web_fetch reads docs as text; limited to allowed_hosts above.
                    {"name": "web_fetch", "enabled": True},
                    {"name": "web_search", "enabled": False},
                ],
            }
        ],
    }


def digest(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True).encode()).hexdigest()[:16]


def main():
    client = anthropic.Anthropic()
    state = json.loads(STATE_FILE.read_text()) if STATE_FILE.exists() else {}
    apps = load_apps()

    env_config = environment_config(apps)
    if "environment_id" not in state:
        env = client.beta.environments.create(name=ENV_NAME, config=env_config)
        state["environment_id"] = env.id
        print(f"Created environment {env.id}")
    elif state.get("environment_digest") != digest(env_config):
        client.beta.environments.update(state["environment_id"], config=env_config)
        print(f"Updated environment {state['environment_id']}")
    state["environment_digest"] = digest(env_config)

    fields = agent_fields()
    if "agent_id" not in state:
        agent = client.beta.agents.create(**fields)
        state.update(agent_id=agent.id, agent_version=agent.version)
        print(f"Created agent {agent.id} (version {agent.version})")
    elif state.get("agent_digest") != digest(fields):
        agent = client.beta.agents.update(state["agent_id"], version=state["agent_version"], **fields)
        state["agent_version"] = agent.version
        print(f"Updated agent {agent.id} to version {agent.version}")
    else:
        print(f"Agent {state['agent_id']} (version {state['agent_version']}) is up to date")
    state["agent_digest"] = digest(fields)

    STATE_FILE.write_text(json.dumps(state, indent=2) + "\n")


if __name__ == "__main__":
    main()
