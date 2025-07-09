#!/bin/bash
# Quick setup script for local development

echo "Setting up Install MCP repository..."

# Make scripts executable
chmod +x install.sh
chmod +x test_meta_mcp.py

echo "✅ Scripts are now executable"
echo ""
echo "Next steps:"
echo "1. Replace 'ddfourtwo' with your GitHub username in all files"
echo "2. Initialize git: git init"
echo "3. Add files: git add ."
echo "4. Commit: git commit -m 'Initial commit'"
echo "5. Create repo on GitHub named 'install-mcp'"
echo "6. Add remote: git remote add origin https://github.com/ddfourtwo/install-mcp.git"
echo "7. Push: git push -u origin main"
echo "8. Enable GitHub Pages in repo settings"
echo ""
echo "Your site will be live at: https://ddfourtwo.github.io/install-mcp/"
