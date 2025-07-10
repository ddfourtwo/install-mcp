# Install-MCP: Disable/Enable and Uninstall Features Implementation Plan

## Overview
This document outlines the implementation plan for adding disable/enable and uninstall functionality to the install-mcp MCP server. These features will allow users to temporarily disable servers without removing them, and completely uninstall servers with proper cleanup.

## Feature 1: Disable/Enable Servers

### 1.1 Requirements
- Ability to disable a server without removing its files or configuration
- Disabled servers should remain in central config but marked as disabled
- Disabled servers should be removed from all MCP client configurations
- Easy re-enabling of disabled servers
- Clear visual indication of disabled status in listings

### 1.2 Implementation Details

#### 1.2.1 Central Configuration Schema Update
Modify `mcp-servers-config.json` to support disabled state:
```json
{
  "servers": {
    "example-server": {
      "name": "example-server",
      "config": { ... },
      "installed_at": "2025-01-10T00:00:00.000Z",
      "disabled": true,  // New field
      "disabled_at": "2025-01-10T12:00:00.000Z"  // New field
    }
  }
}
```

#### 1.2.2 New MCP Tools
Add two new tools to `meta_mcp_server.py`:

1. **`disable_server`**
   - Parameters: `server_name: str`, `reason: Optional[str]`
   - Actions:
     - Set `disabled: true` in central config
     - Record `disabled_at` timestamp
     - Store optional disable reason
     - Call `configure_mcp_clients` with remove flag
     - Keep server files intact
   - Returns: Status message with affected clients

2. **`enable_server`**
   - Parameters: `server_name: str`
   - Actions:
     - Remove `disabled` field from central config
     - Remove `disabled_at` timestamp
     - Call `configure_mcp_clients` to re-add to clients
   - Returns: Status message with updated clients

#### 1.2.3 Update Existing Tools
- **`list_mcp_servers`**: 
  - Show disabled status with visual indicator (e.g., "⚠️ DISABLED")
  - Include disable reason if available
  - Sort disabled servers separately or highlight them

- **`sync_from_central_config`**:
  - Skip disabled servers when syncing
  - Log which servers are skipped due to disabled status

### 1.3 User Experience
```bash
# Disable a server
"Disable the github-mcp server"
> Disabling github-mcp...
> ✅ Server disabled and removed from 4 clients
> Reason: Not currently needed

# List servers (showing disabled)
"List my MCP servers"
> Active servers:
>   ✅ sentry-mcp
>   ✅ linear-mcp
> 
> Disabled servers:
>   ⚠️  github-mcp (disabled on 2025-01-10)

# Enable a server
"Enable the github-mcp server"
> ✅ Server enabled and configured in 4 clients
```

## Feature 2: Uninstall Servers

### 2.1 Requirements
- Complete removal of server files, configuration, and secrets
- Backup option before deletion
- Confirmation prompt for destructive actions
- Clean removal from all locations
- Support for different server types (npm, local, etc.)

### 2.2 Implementation Details

#### 2.2.1 New MCP Tool
Add `uninstall_server` tool to `meta_mcp_server.py`:

**`uninstall_server`**
- Parameters:
  ```python
  server_name: str
  create_backup: bool = True
  force: bool = False  # Skip confirmation
  remove_secrets: bool = True
  ```
- Actions:
  1. Verify server exists
  2. Show what will be deleted (dry run)
  3. Create backup if requested
  4. Remove from all MCP client configs
  5. Remove from central config
  6. Delete server directory
  7. Remove associated secrets from .env
  8. Log uninstallation in history
- Returns: Detailed status with backup location if created

#### 2.2.2 Backup System
Create backups before deletion:
- Location: `~/mcp-servers/.backups/[server-name]-[timestamp]/`
- Contents:
  - Server files (entire directory)
  - Configuration snapshot
  - Associated secrets (encrypted)
  - Installation history

#### 2.2.3 Server Type Handling
Different cleanup for different server types:

1. **NPM Packages** (`npx` command):
   - Clear npm cache for the package
   - No local files to delete

2. **Local Installations** (git clones):
   - Delete entire server directory
   - Remove any generated files

3. **Python Servers**:
   - Remove virtual environments if present
   - Clean up pip cache

#### 2.2.4 Secret Cleanup
Smart secret removal from `.env`:
- Identify all secrets with server prefix (e.g., `GITHUB_TOKEN` for `github` server)
- Prompt user to confirm each secret deletion
- Option to keep secrets for potential reinstallation

### 2.3 Safety Features

#### 2.3.1 Confirmation Prompts
```
You are about to uninstall 'github-mcp'. This will:
- Remove configuration from 4 MCP clients
- Delete /Users/daniel/mcp-servers/github-mcp/ (256 MB)
- Remove 3 secrets from .env file
- Remove from central configuration

A backup will be created at: ~/.mcp-servers/.backups/github-mcp-20250110-120000/

Continue? (yes/no): 
```

#### 2.3.2 Dependency Checking
- Warn if other servers might depend on this one
- Check for shared resources or configurations

### 2.4 User Experience
```bash
# Uninstall with backup
"Uninstall the github-mcp server"
> 🔍 Analyzing github-mcp...
> This will remove:
>   - Configuration from 4 clients
>   - 256 MB of files
>   - 3 secrets (GITHUB_TOKEN, GITHUB_ORG, GITHUB_REPO)
> 
> Create backup? (Y/n): Y
> ✅ Backup created: ~/.mcp-servers/.backups/github-mcp-20250110/
> 
> Proceed with uninstallation? (y/N): y
> ✅ Removed from client configurations
> ✅ Deleted server files
> ✅ Removed secrets
> ✅ Updated central configuration
> 
> Server 'github-mcp' has been completely uninstalled.

# Quick uninstall for npm packages
"Uninstall browser-tools-mcp"
> 🔍 Analyzing browser-tools-mcp (npm package)...
> This will remove configuration from 4 clients.
> No local files or secrets to remove.
> 
> Proceed? (y/N): y
> ✅ Removed from all configurations
> ✅ Server uninstalled successfully
```

## Feature 3: Additional Enhancements

### 3.1 Batch Operations
- `disable_servers`: Disable multiple servers at once
- `uninstall_servers`: Batch uninstall with single confirmation

### 3.2 Status Management
Add server lifecycle states:
- `installed`: Normal active state
- `disabled`: Temporarily deactivated
- `failed`: Installation failed or server broken
- `pending_uninstall`: Marked for removal

### 3.3 Recovery Tools
- `restore_from_backup`: Restore an uninstalled server
- `repair_server`: Fix broken installations

## Implementation Priority

### Phase 1: Disable/Enable (Week 1)
1. Update central config schema
2. Implement `disable_server` tool
3. Implement `enable_server` tool
4. Update `list_mcp_servers` for disabled status
5. Update `sync_from_central_config`

### Phase 2: Basic Uninstall (Week 2)
1. Implement `uninstall_server` tool
2. Add confirmation prompts
3. Basic file and config removal
4. Update central config handling

### Phase 3: Advanced Features (Week 3)
1. Implement backup system
2. Add secret cleanup with confirmation
3. Server type-specific handling
4. Batch operations

### Phase 4: Polish & Testing (Week 4)
1. Recovery tools
2. Comprehensive error handling
3. Documentation
4. Integration tests

## Technical Considerations

### 1. Backwards Compatibility
- Ensure old config files without `disabled` field work correctly
- Migrate existing configs smoothly

### 2. Error Handling
- Graceful handling of partially installed servers
- Recovery from failed uninstallations
- Network issues during npm package operations

### 3. Performance
- Efficient backup creation for large servers
- Batch operations to reduce client restart requirements

### 4. Security
- Secure backup of secrets
- Proper permission handling for file operations
- Audit trail of all operations

## Success Metrics
- Users can disable/enable servers without data loss
- Complete uninstallation leaves no orphaned files or configs
- Backup/restore cycle works reliably
- Operations are intuitive and safe by default
- Clear feedback throughout all operations

## Future Enhancements
- GUI integration for server management
- Automatic cleanup of old backups
- Server health monitoring
- Dependency resolution for complex setups
- Export/import server configurations