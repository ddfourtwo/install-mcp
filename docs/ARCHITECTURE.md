# Install MCP Architecture

This document provides a technical overview of the Install MCP system architecture, including component interactions, data flows, and design decisions.

## Table of Contents
- [System Overview](#system-overview)
- [Core Components](#core-components)
- [Data Flow Diagrams](#data-flow-diagrams)
- [Storage Architecture](#storage-architecture)
- [Security Architecture](#security-architecture)
- [Integration Points](#integration-points)

## System Overview

Install MCP is a meta-MCP server that manages other MCP servers through an agent-first interface. It provides a unified way to install, configure, and manage MCP servers across multiple clients.

```mermaid
graph TB
    subgraph "User Interaction"
        User[User] --> AI[AI Assistant]
    end
    
    subgraph "Install MCP Server"
        AI --> MetaMCP[Meta MCP Server]
        MetaMCP --> Tools[Management Tools]
        Tools --> Installer[Installer]
        Tools --> ConfigMgr[Config Manager]
        Tools --> SecretMgr[Secret Manager]
    end
    
    subgraph "Storage Layer"
        ConfigMgr --> CentralConfig[mcp-servers-config.json]
        SecretMgr --> CentralEnv[.env file]
        Installer --> ServerDirs[Server Directories]
    end
    
    subgraph "MCP Clients"
        ConfigMgr --> Claude[Claude Desktop]
        ConfigMgr --> Cursor[Cursor]
        ConfigMgr --> Windsurf[Windsurf]
        ConfigMgr --> ClaudeCode[Claude Code]
    end
    
    style User fill:#e1f5e1
    style AI fill:#e1f5e1
    style MetaMCP fill:#ffe1e1
    style CentralConfig fill:#e1e1ff
    style CentralEnv fill:#ffe1ff
```

## Core Components

### 1. Meta MCP Server (`meta_mcp_server.py`)

The central server that provides tools for managing other MCP servers.

```mermaid
classDiagram
    class MetaMCPServer {
        +FastMCP mcp
        +Path MCP_BASE_DIR
        +Path MCP_CENTRAL_CONFIG
        +Path MCP_CENTRAL_ENV
        +Dict MCP_CLIENT_CONFIGS
        +list_mcp_servers()
        +execute_in_mcp_directory()
        +collect_secrets()
        +add_server_to_central_config()
        +configure_mcp_clients()
        +sync_from_central_config()
        +export_mcp_setup()
    }
    
    class CentralConfig {
        +Dict servers
        +Dict metadata
        +load_central_config()
        +save_central_config()
    }
    
    class SecretManager {
        +load_central_env()
        +save_to_central_env()
        +resolve_env_placeholders()
    }
    
    class ClientConfigurator {
        +update_client_config()
        +backup_config()
        +resolve_placeholders()
    }
    
    MetaMCPServer --> CentralConfig
    MetaMCPServer --> SecretManager
    MetaMCPServer --> ClientConfigurator
```

### 2. Installation Scripts

Platform-specific installers that set up the Install MCP server.

```mermaid
graph LR
    subgraph "Installation Process"
        A[Download Script] --> B{Platform?}
        B -->|macOS/Linux| C[install.sh]
        B -->|Windows| D[install.ps1]
        
        C --> E[Check Prerequisites]
        D --> E
        E --> F[Create Directories]
        F --> G[Download Server Files]
        G --> H[Install Dependencies]
        H --> I[Configure Clients]
        I --> J[Install Helper Tools]
    end
```

### 3. Secret Collection System

Secure web-based interface for collecting API keys and secrets.

```mermaid
sequenceDiagram
    participant User
    participant AI
    participant MetaMCP
    participant WebServer
    participant Browser
    participant EnvFile
    
    User->>AI: "Install GitHub server"
    AI->>MetaMCP: collect_secrets("github", secrets)
    MetaMCP->>WebServer: Start local server
    MetaMCP->>Browser: Open localhost:8901
    Browser->>User: Show secret form
    User->>Browser: Enter API key
    Browser->>WebServer: POST /submit
    WebServer->>EnvFile: Save namespaced secret
    WebServer->>MetaMCP: Return success
    MetaMCP->>AI: Secrets collected
    AI->>User: GitHub server configured!
```

## Data Flow Diagrams

### Server Installation Flow

```mermaid
graph TD
    A[User Request] --> B[AI Interprets]
    B --> C{Server Type?}
    
    C -->|NPM Package| D[No Download Needed]
    C -->|GitHub Node.js| E[Clone Repository]
    C -->|GitHub Python| F[Clone Repository]
    
    E --> G[npm install]
    F --> H[pip install]
    
    G --> I[Build if needed]
    H --> J[Configure Python]
    
    D --> K[Add to Central Config]
    I --> K
    J --> K
    
    K --> L{Needs Secrets?}
    L -->|Yes| M[Collect Secrets]
    L -->|No| N[Configure Clients]
    M --> N
    
    N --> O[Update All Clients]
    O --> P[Ready to Use]
```

### Configuration Synchronization

```mermaid
graph LR
    subgraph "Central Storage"
        A[mcp-servers-config.json]
        B[.env secrets]
    end
    
    subgraph "Resolution Process"
        C[Load Config]
        D[Resolve Placeholders]
        E[Apply Namespacing]
    end
    
    subgraph "Client Updates"
        F[Claude Desktop]
        G[Cursor]
        H[Windsurf]
        I[Claude Code]
    end
    
    A --> C
    B --> D
    C --> D
    D --> E
    E --> F
    E --> G
    E --> H
    E --> I
```

## Storage Architecture

### Directory Structure

```
~/mcp-servers/
├── install-mcp/                 # Meta MCP server
│   ├── meta_mcp_server.py      # Main server
│   ├── multi_secret_collector.py # Secret collection
│   └── .mcp_command_history.json # Installation history
├── mcp-servers-config.json      # Central configuration
├── .env                         # Central secrets
└── [server-name]/               # Installed servers
    ├── .git/                    # If from GitHub
    ├── package.json             # If Node.js
    ├── requirements.txt         # If Python
    └── .mcp_command_history.json # Server-specific history
```

### Configuration Schema

```json
{
  "version": "1.0",
  "servers": {
    "server-name": {
      "name": "server-name",
      "config": {
        "command": "node|python3|npx",
        "args": ["path/to/server"],
        "env": {
          "VAR_NAME": "VAR_NAME.env"  // Placeholder
        }
      },
      "installed_at": "ISO-8601 timestamp",
      "required_env_vars": ["API_KEY", "API_SECRET"]
    }
  },
  "metadata": {
    "created": "ISO-8601 timestamp",
    "last_updated": "ISO-8601 timestamp"
  }
}
```

### Secret Storage

Secrets are stored in a central `.env` file with namespacing:

```
# Original variable: API_KEY
# Namespaced variable: SERVERNAME_API_KEY
GITHUB_GITHUB_TOKEN=ghp_xxxxxxxxxxxx
SLACK_SLACK_TOKEN=xoxb-xxxxxxxxxxxx
OPENAI_OPENAI_API_KEY=sk-xxxxxxxxxxxx
```

## Security Architecture

### Secret Collection Security

```mermaid
graph TD
    A[Secret Request] --> B[Local Web Server]
    B --> C{Port 8901}
    C --> D[Localhost Only]
    D --> E[HTTPS Not Required]
    E --> F[Browser Form]
    F --> G[POST to Server]
    G --> H[No Logging]
    H --> I[Direct to .env]
    I --> J[chmod 0600]
    J --> K[Secure Storage]
    
    style H fill:#ffe1e1
    style J fill:#e1ffe1
```

### Security Principles

1. **No Secret Exposure**: Secrets never appear in:
   - AI conversation logs
   - Command history
   - Configuration files (only placeholders)
   - Server responses

2. **Local-Only Collection**: Secret collection web server:
   - Binds to localhost only
   - Uses random high port
   - Auto-closes after collection
   - No external access possible

3. **File Permissions**: 
   - `.env` file: 0600 (owner read/write only)
   - Config files: Standard permissions
   - No secrets in git repositories

## Integration Points

### MCP Client Integration

```mermaid
graph LR
    subgraph "Config Locations"
        A[Claude Desktop macOS<br/>~/Library/Application Support/Claude/]
        B[Claude Desktop Windows<br/>%APPDATA%/Claude/]
        C[Claude Desktop Linux<br/>~/.config/Claude/]
        D[Claude Code<br/>~/.claude.json]
        E[Cursor<br/>~/.cursor/...]
        F[Windsurf<br/>~/.codeium/windsurf/]
    end
    
    subgraph "Config Format"
        G[JSON Structure]
        H[mcpServers Object]
        I[Server Config]
    end
    
    A --> G
    B --> G
    C --> G
    D --> G
    E --> G
    F --> G
    
    G --> H
    H --> I
```

### Server Type Detection

```mermaid
graph TD
    A[Examine Directory] --> B{Has .git?}
    B -->|Yes| C[Git Repository]
    B -->|No| D{Has package.json?}
    
    C --> E[Get Remote URL]
    
    D -->|Yes| F[Node.js Server]
    D -->|No| G{Has requirements.txt?}
    
    G -->|Yes| H[Python Server]
    G -->|No| I[Unknown Type]
    
    F --> J{Has build script?}
    J -->|Yes| K[Needs Build]
    J -->|No| L[Direct Run]
    
    H --> M[Check Python Files]
```

## Design Decisions

### 1. Agent-First Interface
- **Decision**: Use natural language as primary interface
- **Rationale**: Reduces complexity for users, leverages AI capabilities
- **Trade-off**: Requires AI assistant, not suitable for CLI-only workflows

### 2. Central Configuration
- **Decision**: Single source of truth for all MCP servers
- **Rationale**: Simplifies management, enables easy export/import
- **Trade-off**: Additional sync step required

### 3. Namespaced Secrets
- **Decision**: Prefix all env vars with server name
- **Rationale**: Prevents conflicts, clear ownership
- **Trade-off**: Longer variable names

### 4. Web-Based Secret Collection
- **Decision**: Use local web server for secret input
- **Rationale**: Better UX than terminal input, maintains security
- **Trade-off**: Requires browser, more complex than CLI

### 5. Multi-Client Support
- **Decision**: Update all known MCP clients simultaneously
- **Rationale**: Consistent experience across tools
- **Trade-off**: More complex configuration logic

## Future Enhancements

1. **Server Repository**: Central registry of verified MCP servers
2. **Version Management**: Track and update server versions
3. **Dependency Resolution**: Handle server interdependencies
4. **Cloud Sync**: Optional encrypted cloud backup
5. **Team Sharing**: Secure configuration sharing for teams

---

*This architecture document is a living document and will be updated as the system evolves.*
