# MCP UI - Quick Installation Guide

## Prerequisites Check

```bash
# Check Node version (need 20.19+ or 22.12+)
node --version

# Check Python version (need 3.10+)
python3 --version

# Check if in bench directory
pwd  # Should be /home/frappe/bench
```

## Installation Steps

### 1. Upgrade Node.js (if needed)

**Option A: Using nvm (Recommended)**
```bash
# Install nvm if not installed
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
source ~/.bashrc

# Install and use Node 20
nvm install 20
nvm use 20
nvm alias default 20
```

**Option B: Using NodeSource**
```bash
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs
```

Verify:
```bash
node --version  # Should show v20.x.x or v22.x.x
```

### 2. Build Frontend

```bash
cd /home/frappe/bench/apps/mcp_ui/mcp

# Install dependencies
yarn install

# Build production bundle
yarn build

# Verify build output
ls -la ../mcp_ui/public/mcp/
# Should see: index.html, index.js, index.css, logo.svg
```

### 3. Install App on Site

```bash
cd /home/frappe/bench

# Replace 'your-site' with actual site name
bench --site your-site install-app mcp_ui

# You should see:
# - Creating DocTypes...
# - Installing fixtures...
# - MCP UI app installed successfully!
```

### 4. Migrate Database

```bash
bench --site your-site migrate
```

### 5. Clear Cache & Restart

```bash
# Clear all caches
bench --site your-site clear-cache

# Restart bench
bench restart
```

### 6. Verify Installation

```bash
# Check if app is installed
bench --site your-site list-apps
# Should include: mcp_ui

# Check DocTypes created
bench --site your-site console
```

In the console:
```python
>>> frappe.db.get_list("DocType", filters={"module": "Mcp Ui"})
# Should show: MCP User Credits, MCP Usage Log, MCP Credit Package

>>> frappe.db.count("MCP Credit Package")
# Should show: 4 (default packages)

>>> exit()
```

## Access the App

### Method 1: Direct URL
Navigate to: `http://your-site:8000/mcp_ui`

### Method 2: App Launcher
1. Login to Frappe Desk
2. Click the App Launcher icon (grid icon in top-left)
3. Click on "MCP Tools"

## First-Time Usage

### 1. Check Credit Balance
- Top-right corner shows your balance
- New users start with 100 free credits

### 2. Browse Tools
- Click "Tools" in navigation
- Or use the search bar in Simple Mode

### 3. Execute a Tool
1. Click on any tool card
2. Fill in the required parameters
3. Click "Execute"
4. View results and remaining credits

### 4. View History
- Click "History" to see all executions
- See credits consumed per operation

### 5. Purchase More Credits
1. Go to "Credits" page
2. Click "Purchase Credits"
3. Select a package
4. Click "Purchase" (currently a placeholder)

## Troubleshooting

### Frontend Not Loading

**Symptom**: Blank page or 404 at /mcp_ui

**Solutions**:
```bash
# 1. Check if build files exist
ls -la apps/mcp_ui/mcp_ui/public/mcp/

# 2. Rebuild frontend
cd apps/mcp_ui/mcp
yarn build

# 3. Check web page file
ls -la apps/mcp_ui/mcp_ui/www/mcp_ui.html

# 4. Clear cache and restart
cd /home/frappe/bench
bench --site your-site clear-cache
bench restart
```

### Tools Not Executing

**Symptom**: Error when clicking "Execute"

**Solutions**:
```bash
# 1. Check frappe-mcp is installed
bench pip list | grep frappe-mcp

# 2. Reinstall if needed
bench pip install frappe-mcp

# 3. Check logs
bench --site your-site logs
# Press Ctrl+C to exit
```

### Credits Not Showing

**Symptom**: Balance shows 0 or error

**Solutions**:
```bash
bench --site your-site console
```

In console:
```python
>>> from mcp_ui.api.credits import get_balance
>>> get_balance()
# Should create credit record if missing

>>> exit()
```

### App Not in App Launcher

**Solutions**:
```bash
# 1. Check hooks.py configuration
cat apps/mcp_ui/mcp_ui/hooks.py | grep add_to_apps_screen

# 2. Clear cache
bench --site your-site clear-cache

# 3. Reload browser (Ctrl+Shift+R)
```

## Development Mode

For development with hot reload:

```bash
# Terminal 1: Frappe development server
cd /home/frappe/bench
bench start

# Terminal 2: Frontend development server
cd apps/mcp_ui/mcp
yarn dev
```

Access at: `http://localhost:5173` (Vite dev server)

Note: You'll need to update `vite.config.ts` base URL for dev mode.

## Uninstallation

If you need to uninstall:

```bash
# Uninstall from site
bench --site your-site uninstall-app mcp_ui

# Remove app from bench
bench remove-app mcp_ui

# Clean up
rm -rf apps/mcp_ui
```

## Configuration Files

Key files to check if issues occur:

1. **Frontend Build**: `apps/mcp_ui/mcp/vite.config.ts`
2. **App Hooks**: `apps/mcp_ui/mcp_ui/hooks.py`
3. **Web Page**: `apps/mcp_ui/mcp_ui/www/mcp_ui.html`
4. **API Client**: `apps/mcp_ui/mcp/src/lib/api.ts`

## Logs Location

```bash
# Frappe logs
tail -f sites/your-site/logs/web.error.log
tail -f sites/your-site/logs/worker.error.log

# Bench logs
bench --site your-site logs
```

## Support

If you encounter issues:

1. ✅ Check this guide first
2. ✅ Review browser console (F12)
3. ✅ Check Frappe error logs
4. ✅ Verify all prerequisites
5. ✅ Read IMPLEMENTATION_SUMMARY.md for details
6. ✅ Check README.md for architecture

## Success Indicators

Your installation is successful when:

- ✅ `/mcp_ui` loads without errors
- ✅ Credit balance displays in top-right
- ✅ Tools page shows 10 tools
- ✅ You can execute a tool successfully
- ✅ History shows the execution
- ✅ Credits are deducted correctly
- ✅ UI is responsive on mobile

## Next Steps

After successful installation:

1. **Create Custom Tools**: See README.md for examples
2. **Configure Credit Costs**: Edit `api/credits.py`
3. **Add Credit Packages**: Edit `fixtures/credit_packages.py`
4. **Integrate Payment**: Add Stripe/PayPal to PurchaseModal
5. **Customize UI**: Modify components in `mcp/src/`

---

**Need Help?** Check IMPLEMENTATION_SUMMARY.md for complete technical details.

