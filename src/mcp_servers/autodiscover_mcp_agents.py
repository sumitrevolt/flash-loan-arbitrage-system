import os
import yaml

def discover_servers_and_agents(base_dirs, agent_prefix="agent", mcp_prefix="mcp"):
    config = {"services": {}}
    port = 8000
    agent_id = 1

    for base_dir in base_dirs:
        for root, dirs, files in os.walk(base_dir):
            for file in files:
                if file.endswith(".py") and not file.startswith("__"):
                    name = os.path.splitext(file)[0]
                    abs_path = os.path.join(root, file)
                    service_name = name.replace("_", "-")
                    if "agent" in root or "ai_agent" in root:
                        config["services"][f"{agent_prefix}-{service_name}"] = {
                            "build": ".",
                            "command": f"python {abs_path}",
                            "environment": [
                                f"AGENT_ROLE={service_name}",
                                f"AGENT_ID={agent_id}",
                                f"AGENT_PORT={port}"
                            ],
                            "ports": [f"{port}:{port}"]
                        }
                        agent_id += 1
                    else:
                        config["services"][f"{mcp_prefix}-{service_name}"] = {
                            "build": ".",
                            "command": f"python {abs_path}",
                            "environment": [
                                f"MCP_SERVER_TYPE={service_name}",
                                f"MCP_SERVER_NAME={service_name}",
                                f"MCP_PORT={port}"
                            ],
                            "ports": [f"{port}:{port}"]
                        }
                    port += 1
    return config

if __name__ == "__main__":
    # Add more directories as needed
    base_dirs = ["mcp_servers", "ai_agent"]
    config = discover_servers_and_agents(base_dirs)
    with open("autodiscovered-docker-compose.yml", "w") as f:
        yaml.dump(config, f, default_flow_style=False)
    print("Generated autodiscovered-docker-compose.yml") 