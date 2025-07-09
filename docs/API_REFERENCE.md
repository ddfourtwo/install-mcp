# Install MCP API Reference

This document provides detailed information about all available tools in the Install MCP server that AI assistants can use.

## Table of Contents

- [Core Tools](#core-tools)
  - [list_mcp_servers](#list_mcp_servers)
  - [execute_in_mcp_directory](#execute_in_mcp_directory)
  - [collect_secrets](#collect_secrets)
  - [add_server_to_central_config](#add_server_to_central_config)
  - [configure_mcp_clients](#configure_mcp_clients)
- [Synchronization Tools](#synchronization-tools)
  - [sync_from_central_config](#sync_from_central_config)
  - [export_mcp_setup](#export_mcp_setup)

---

## Core Tools

### list_mcp_servers

Lists all installed MCP servers and checks their status.

#### Description
This is typically the first tool to use. It shows what MCP servers are already installed, which ones are configured in MCP clients, and their installation status.

#### Parameters
None

#### Returns
```typescript
{
  base_directory: string,          // Path to ~/mcp-servers/
  total_servers: number,          
  servers: Array<{
    name: string,                  // Server directory name
    path: string,                  // Full path to server
    has_install_script: boolean,
    has_env_file: boolean,
    has_node_modules: boolean,
    has_package_json: boolean,
    has_python_server: boolean,
    files: number,                 // File count in directory
    configured_in_clients: string[], // Which clients have this server
    is_configured: boolean,
    configuration?: {              // Current configuration if configured
      command: string,
      args: string[],
      env: object
    },
    installation_type?: string,    // "git" | "npm" | etc
    source_url?: string,          // Git URL if applicable
    npm_package?: string,         // NPM package name if applicable
    server_type?: string,         // "node" | "python"
    required_secrets?: string[],  // Required environment variables
    installation_history?: Array<{
      timestamp: string,
      command: string,
      success: boolean
    }>
  }>,
  central_config: {
    exists: boolean,
    path: string,
    servers_in_config: number,
    last_updated: string
  },
  replication_instructions: string[]
}
```

#### Example Usage
```
AI: "I'll check what MCP servers you have installed."
Tool: list_mcp_servers()
Response: Shows GitHub, Slack, and filesystem servers are installed.
```

---

### execute_in_mcp_directory

Execute shell commands to install MCP servers within the `~/mcp-servers/` directory.

#### Description
This tool is used for running installation commands like git clone, npm install, pip install, etc. It ensures all operations happen within the MCP servers directory for safety.

#### Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| command | string | Yes | Shell command to execute |
| working_dir | string | No | Subdirectory within ~/mcp-servers/ (empty string for base dir) |
| timeout | number | No | Command timeout in seconds (default: 300) |

#### Returns
```typescript
{
  command: string,              // The executed command
  working_directory: string,    // Full path where command was run
  stdout: string,              // Command output
  stderr: string,              // Error output
  return_code: number,         // Exit code (0 = success)
  success: boolean,            // Whether command succeeded
  next_action?: string         // Suggested next step
}
```

#### Installation Patterns

##### GitHub Node.js Server
```python
# 1. Clone repository
execute_in_mcp_directory("git clone https://github.com/user/repo-name server-name", "")

# 2. Install dependencies  
execute_in_mcp_directory("npm install", "server-name")

# 3. Build if needed
execute_in_mcp_directory("npm run build", "server-name")
```

##### GitHub Python Server
```python
# 1. Clone repository
execute_in_mcp_directory("git clone https://github.com/user/repo-name server-name", "")

# 2. Install dependencies
execute_in_mcp_directory("pip install -r requirements.txt", "server-name")
```

##### Check Installation
```python
# List files in server directory
execute_in_mcp_directory("ls -la", "server-name")

# Check package.json
execute_in_mcp_directory("cat package.json", "server-name")

# Check README
execute_in_mcp_directory("cat README.md", "server-name")
```

#### Example Usage
```
AI: "I'll install the GitHub MCP server for you."
Tool: execute_in_mcp_directory("git clone https://github.com/modelcontextprotocol/servers github", "")
Response: Successfully cloned repository
Tool: execute_in_mcp_directory("npm install", "github")
Response: Dependencies installed
```

---

### collect_secrets

Collect API keys and secrets via a secure web interface.

#### Description
Opens a local web server that provides a secure form for entering secrets. Secrets are saved to the central .env file with proper namespacing and are never exposed in the conversation.

#### Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| server_name | string | Yes | Name of the MCP server needing secrets |
| secrets | string | Yes | JSON string with secret definitions |

#### Secret Definition Format
```typescript
// Single secret
{
  "name": "API_KEY",
  "description": "Your API Key"
}

// Multiple secrets
[
  {
    "name": "API_KEY",
    "description": "Your API Key"
  },
  {
    "name": "API_SECRET", 
    "description": "Your API Secret"
  }
]
```

#### Returns
```typescript
{
  success: boolean,
  status: "all_collected" | "partial_collection" | "manual_required" | "collector_error",
  message: string,
  saved_secrets?: string[],      // Names of successfully saved secrets
  missing_secrets?: string[],    // Names of secrets that failed
  env_file: string,             // Path to .env file
  next_steps?: string[],        // What to do next
  instructions?: string[]       // Manual instructions if web collection fails
}
```

#### Namespacing
Secrets are automatically namespaced to prevent conflicts:
- Input: `API_KEY` for server `github`
- Stored as: `GITHUB_API_KEY`

#### Example Usage
```python
# Single secret
collect_secrets("github", '{"name": "GITHUB_TOKEN", "description": "GitHub Personal Access Token"}')

# Multiple secrets
collect_secrets("openai", '[{"name": "OPENAI_API_KEY", "description": "OpenAI API Key"}, {"name": "OPENAI_ORG_ID", "description": "OpenAI Organization ID"}]')
```

---

### add_server_to_central_config

Add a new MCP server to the central configuration.

#### Description
Saves the server configuration centrally with placeholders for environment variables. This must be called before `configure_mcp_clients()`.

#### Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| server_name | string | Yes | Unique identifier for the server |
| command | string | Yes | Executable command (npx, node, python3, or full path) |
| args | string | Yes | JSON array of arguments as a string |
| required_env_vars | string | No | JSON array of required env var names |
| env_vars | string | No | JSON object of non-secret env vars |

#### Command Formats by Server Type

##### NPM Package
```python
add_server_to_central_config(
    "context7",
    "npx",
    '["-y", "@upstash/context7-mcp@latest"]',
    None,
    None
)
```

##### Local Node.js Server
```python
add_server_to_central_config(
    "github",
    "node",
    '["/Users/username/mcp-servers/github/dist/index.js"]',
    '["GITHUB_TOKEN"]',
    '{"NODE_ENV": "production"}'
)
```

##### Local Python Server
```python
add_server_to_central_config(
    "my-python-server",
    "python3",
    '["/Users/username/mcp-servers/my-python-server/server.py"]',
    '["API_KEY", "API_SECRET"]',
    None
)
```

#### Returns
```typescript
{
  success: boolean,
  message: string,
  server_name: string,
  central_config_path: string,
  config_saved: {
    command: string,
    args: string[],
    env?: object
  },
  next_steps: string[]    // Usually collect_secrets() and configure_mcp_clients()
}
```

#### Environment Variable Placeholders
Environment variables are stored as placeholders that get resolved from the central .env:
```json
{
  "env": {
    "GITHUB_TOKEN": "GITHUB_TOKEN.env"  // Placeholder format
  }
}
```

---

### configure_mcp_clients

Configure an MCP server in all clients from central configuration.

#### Description
Reads server config from central configuration, resolves environment variables, and updates all MCP client configurations. Creates backups before making changes.

#### Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| server_name | string | Yes | Name of server to configure (must exist in central config) |

#### Returns
```typescript
{
  success: boolean,
  server_name: string,
  updated_clients: string[],     // Clients successfully updated
  skipped_clients: string[],     // Clients not installed
  errors: string[],              // Any errors encountered
  message: string,
  test_prompts?: string[],       // Suggested prompts to test the server
  next_steps?: string[]          // What to do after configuration
}
```

#### Client Locations
The tool updates configurations in these locations:
- **Claude Desktop macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Claude Desktop Windows**: `%APPDATA%/Claude/claude_desktop_config.json`
- **Claude Desktop Linux**: `~/.config/Claude/claude_desktop_config.json`
- **Claude Code**: `~/.claude.json`
- **Cursor**: `~/.cursor/User/globalStorage/cursor-ai.cursor-ai/config.json`
- **Windsurf**: `~/.codeium/windsurf/mcp_config.json`

#### Example Usage
```
AI: "I'll configure the GitHub server in all your MCP clients."
Tool: configure_mcp_clients("github")
Response: Updated Claude Desktop and Cursor, created backups
AI: "Please restart your MCP client and try: 'List my GitHub repositories'"
```

---

## Synchronization Tools

### sync_from_central_config

Sync all MCP client configurations from the central config file.

#### Description
Reads the central `mcp-servers-config.json` and updates all MCP clients to match. Useful for applying config changes across all clients at once or setting up a new machine.

#### Parameters
None

#### Returns
```typescript
{
  success: boolean,
  message: string,
  synced_servers: string[],      // Server names that were synced
  updated_clients: string[],     // Clients that were updated
  errors: string[],              // Any errors encountered
  central_config_path: string,
  next_steps?: string[]
}
```

#### Use Cases
1. Apply configuration changes to all clients at once
2. Restore configurations after client updates
3. Set up a new machine from existing config
4. Ensure consistency across all clients

#### Example Usage
```
AI: "I'll sync all your MCP servers across all clients."
Tool: sync_from_central_config()
Response: Synced 5 servers to 3 clients
```

---

### export_mcp_setup

Export complete MCP setup for sharing or replication.

#### Description
Gathers all information needed to replicate your exact MCP setup on another machine, including installed servers, configurations, installation commands, and required environment variables (without exposing secrets).

#### Parameters
None

#### Returns
```typescript
{
  success: boolean,
  message: string,
  total_servers: number,
  setup_info: {
    export_timestamp: string,
    mcp_base_directory: string,
    servers: Array<{
      name: string,
      directory: string,
      installation_commands: string[],  // History of install commands
      configuration: object,            // Server configuration
      required_secrets: string[],       // Required env vars (names only)
      git_url?: string                 // Source repository if applicable
    }>,
    central_config_path: string,
    central_env_path: string
  },
  replication_instructions: string,    // Step-by-step markdown instructions
  notes: string[]
}
```

#### Generated Instructions Include
1. Prerequisites and setup steps
2. Automated installation commands for each server
3. Configuration commands with proper arguments
4. Secret collection steps (without exposing values)
5. Final client configuration steps
6. Manual configuration fallbacks

#### Example Usage
```
AI: "I'll export your complete MCP setup."
Tool: export_mcp_setup()
Response: Returns detailed instructions for replicating the setup
AI: "Here's your complete MCP setup. Save these instructions to share with your team or set up a new machine."
```

---

## Common Workflows

### Installing a New Server

1. **Check Current State**
   ```
   list_mcp_servers()
   ```

2. **Install Server** (example: GitHub server)
   ```
   execute_in_mcp_directory("git clone https://github.com/modelcontextprotocol/servers github", "")
   execute_in_mcp_directory("npm install", "github")
   execute_in_mcp_directory("npm run build", "github")
   ```

3. **Add to Central Config**
   ```
   add_server_to_central_config("github", "node", '["/Users/username/mcp-servers/github/dist/index.js"]', '["GITHUB_TOKEN"]')
   ```

4. **Collect Secrets**
   ```
   collect_secrets("github", '{"name": "GITHUB_TOKEN", "description": "GitHub Personal Access Token"}')
   ```

5. **Configure Clients**
   ```
   configure_mcp_clients("github")
   ```

### Sharing Your Setup

1. **Export Setup**
   ```
   export_mcp_setup()
   ```

2. **Share the instructions** with your team

3. **On new machine**, they follow the generated instructions

### Updating All Clients

```
sync_from_central_config()
```

---

## Error Handling

All tools return structured errors that help diagnose issues:

- **File/Directory Not Found**: Check paths and ensure directories exist
- **Permission Denied**: Check file permissions, especially for .env file
- **Command Failed**: Review stdout/stderr in the response
- **JSON Parse Errors**: Ensure proper JSON formatting in string parameters
- **Configuration Not Found**: Server must be added to central config first

## Best Practices

1. **Always run `list_mcp_servers()` first** to understand current state
2. **Check command success** before proceeding to next step
3. **Use namespaced environment variables** to prevent conflicts
4. **Create backups** before major changes (automatic for client configs)
5. **Test servers after installation** with the suggested prompts
6. **Document custom servers** in their own README files

---

*This API reference covers version 0.1.0 of Install MCP. Check the [GitHub repository](https://github.com/ddfourtwo/install-mcp) for updates.*
