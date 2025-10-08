# MCP UI - Model Context Protocol Interface for Frappe

A modern, user-friendly interface for executing MCP (Model Context Protocol) tools in Frappe Framework with AI-powered natural language processing and a credit-based system.

## Features

### 🤖 **AI-Powered Natural Language Interface** ⭐ NEW!
- **OpenAI Function Calling**: Use GPT-4o, GPT-4o-mini for intelligent tool mapping
- **Anthropic Tool Use**: Leverage Claude 3 (Opus, Sonnet, Haiku) for natural language understanding
- **Smart Forms**: Automatically generate user-friendly forms from DocType schemas
- **No JSON Required**: Business users can use plain English instead of writing JSON
- **Bulk Operations**: Create/update/delete multiple records with natural language

### ⌨️ **Keyboard Shortcuts** ⭐ NEW!
- `Cmd/Ctrl + K`: Quick Search
- `Cmd/Ctrl + N`: Create New
- `Cmd/Ctrl + 1-6`: Navigate between pages
- `Cmd/Ctrl + B`: Toggle Sidebar
- `?`: Show all keyboard shortcuts

### 🎯 **Dual Interface Modes**
- **Simple Mode**: Natural language input for quick operations, perfect for non-technical users
- **Advanced Mode**: Full-featured interface with sidebar navigation and detailed controls

### 💳 **Credit-Based System**
- Pre-purchased credit packages
- Real-time credit balance tracking
- Detailed usage history and analytics
- Flexible pricing tiers (Starter, Professional, Business, Enterprise)

### 🛠️ **10+ MCP Tools**

#### CRUD Operations
- **Create Document**: Create new documents in any DocType (with smart forms!)
- **Update Document**: Modify existing documents (with smart forms!)
- **Delete Document**: Remove documents (destructive operation)
- **Get Document**: Fetch single document details

#### Query & Search
- **Get List**: Retrieve filtered document lists
- **Search Documents**: Full-text search across DocTypes

#### Advanced Operations
- **Execute Report**: Run Frappe reports with filters
- **Bulk Create**: Create multiple documents at once ⭐ NEW!
- **Bulk Update**: Update multiple documents simultaneously ⭐ NEW!
- **Bulk Delete**: Delete multiple documents ⭐ NEW!
- **Import CSV**: Import data from CSV files ⭐ NEW!
- **Export Data**: Export data in JSON/CSV format
- **Get Dashboard Data**: Retrieve dashboard statistics

### 🔍 **System Discovery**
- Browse installed Frappe apps
- View available DocTypes and their metadata
- Explore custom fields and workflows
- System-wide statistics

### 🎨 **Modern UI/UX**
- Built with React, TypeScript, and Vite
- Shadcn/ui components for consistent design
- Tailwind CSS for responsive layouts
- Framer Motion animations
- Confetti effects on successful operations
- Toast notifications for feedback
- Keyboard shortcuts for power users

### 📊 **Usage Tracking**
- Detailed execution logs
- Success/failure status tracking
- Input/output recording
- Error message capture
- Timeline visualization

## Installation

### Prerequisites
- Frappe Framework v15.x or higher
- Node.js v20.19+ or v22.12+
- Python 3.10+

### Steps

1. **Get the app:**
   ```bash
   bench get-app https://github.com/yourusername/mcp_ui
   ```

2. **Install on site:**
   ```bash
   bench --site your-site install-app mcp_ui
   ```

3. **Install AI dependencies (optional, for NLP features):**
   ```bash
   # For OpenAI support
   bench pip install openai
   
   # For Anthropic support
   bench pip install anthropic
   ```

4. **Build frontend:**
   ```bash
   cd apps/mcp_ui/mcp
   yarn install
   yarn build
   ```

5. **Migrate and restart:**
   ```bash
   bench --site your-site migrate
   bench restart
   ```

## Usage

### Accessing the App

1. Navigate to `/mcp` in your Frappe site
2. Or access via the App Launcher in Frappe Desk (MCP Tools icon)

### First-Time Setup

1. **Initial Credits**: New users receive 100 free credits automatically
2. **Configure AI (Optional)**: Go to MCP Settings to enable OpenAI or Anthropic
3. **Browse Tools**: Explore available tools in the Tools page
4. **Execute Tools**: Click on any tool card or use natural language
5. **Monitor Usage**: Track your usage in the History page

### AI Configuration (Optional)

#### Using OpenAI

1. Get an API key from [OpenAI Platform](https://platform.openai.com/)
2. Go to **Frappe Desk → MCP Settings**
3. Check **Enable AI-Powered NLP** ✅
4. Select **AI Provider: OpenAI**
5. Enter your **OpenAI API Key**
6. Select **Model** (recommended: `gpt-4o-mini` for best cost/performance)
7. Save

**Latest Models & Costs:**
- `gpt-4o`: $2.50 per 1M input tokens - Most capable
- `gpt-4o-mini`: $0.15 per 1M input tokens - **Recommended** for cost efficiency
- `o1-preview`: $15 per 1M input tokens - Advanced reasoning
- `o1-mini`: $3 per 1M input tokens - Affordable reasoning

**Note:** All OpenAI models require a paid API account. There are no free tiers for API usage.

#### Using Anthropic

1. Get an API key from [Anthropic Console](https://console.anthropic.com/)
2. Go to **Frappe Desk → MCP Settings**
3. Check **Enable AI-Powered NLP** ✅
4. Select **AI Provider: Anthropic**
5. Enter your **Anthropic API Key**
6. Select **Model** (recommended: `claude-3-5-haiku-20241022` for best speed/cost)
7. Save

**Latest Models & Costs:**
- `claude-3-5-sonnet-20241022`: $3 per 1M input tokens - Most capable Claude
- `claude-3-5-haiku-20241022`: $1 per 1M input tokens - **Recommended** for speed & cost
- `claude-3-opus-20240229`: $15 per 1M input tokens - Powerful legacy model

**Note:** All Anthropic models require a paid API account. There are no free tiers for API usage.

### Natural Language Usage (Simple Mode)

Once AI is configured, you can use plain English:

**Examples:**

| What You Type | What Happens |
|---------------|-------------|
| "Create a new customer" | Opens Customer creation form |
| "Show me all items" | Lists all items |
| "Search for John in customers" | Searches for "John" in Customer DocType |
| "I need sales order statistics" | Shows Sales Order dashboard |
| "Create 50 test items" | Opens bulk creation for 50 items |
| "Export all customers to CSV" | Exports customer data |

**How It Works:**

1. **User types in plain English** (e.g., "create a customer named John")
2. **AI analyzes the request** using OpenAI Function Calling or Anthropic Tool Use
3. **AI identifies the tool** (e.g., `create_document`)
4. **AI extracts parameters** (e.g., `doctype: "Customer"`)
5. **System shows smart form** - user fills in fields (NO JSON!)
6. **User submits** - document created!

### Advanced Mode

For power users who prefer direct control:

1. Switch to **Advanced Mode** in top bar
2. Use the **Tools page** to browse all available tools
3. Click on a tool card
4. Fill in parameters using:
   - **Smart Forms** for create/update operations
   - **Simple inputs** for other operations
5. Execute and view results

### Purchasing Credits

1. Go to the Credits page
2. Click "Purchase Credits"
3. Select a credit package
4. Complete the purchase (payment integration required)

### Keyboard Shortcuts

Press `?` anywhere to see all shortcuts, or use:

- `Cmd/Ctrl + K`: Quick search
- `Cmd/Ctrl + 1`: Go to Dashboard
- `Cmd/Ctrl + 2`: Go to Tools
- `Cmd/Ctrl + 3`: Go to History
- `Cmd/Ctrl + N`: Create new
- `ESC`: Close dialogs

## Architecture

### Backend (Python)

```
mcp_ui/
├── mcp_server/
│   ├── mcp.py              # MCP server instance
│   ├── core_tools.py       # 10 core tool implementations
│   └── dynamic_tools.py    # Dynamic tool generation
├── api/
│   ├── credits.py          # Credit management APIs
│   ├── tools.py            # Tool execution APIs
│   ├── discovery.py        # System discovery APIs
│   ├── form_builder.py     # Smart form generation ⭐ NEW!
│   ├── nlp_processor.py    # Basic NLP (fallback) ⭐ NEW!
│   ├── ai_nlp.py           # OpenAI/Anthropic integration ⭐ NEW!
│   └── bulk_operations.py  # Bulk CRUD operations ⭐ NEW!
├── doctype/
│   ├── mcp_user_credits/   # Credit balance tracking
│   ├── mcp_usage_log/      # Execution history
│   ├── mcp_credit_package/ # Credit packages
│   └── mcp_settings/       # Global settings ⭐ NEW!
└── fixtures/
    └── credit_packages.py  # Default packages
```

### Frontend (React + TypeScript)

```
mcp/src/
├── components/
│   ├── layout/                # AppShell, TopBar, Sidebar
│   │   └── KeyboardShortcutsModal.tsx  # ⭐ NEW!
│   ├── tools/                 # ToolCard, ToolGrid, ToolExecutor
│   │   └── SmartForm.tsx      # Dynamic form builder ⭐ NEW!
│   ├── modes/
│   │   └── NaturalLanguageInput.tsx   # NLP interface ⭐ NEW!
│   ├── credits/               # CreditBalance, CreditHistory, PurchaseModal
│   └── ui/                    # Shadcn/ui components
├── pages/
│   ├── Dashboard.tsx          # Home page (with NLP)
│   ├── Tools.tsx              # Tool marketplace
│   ├── History.tsx            # Usage history
│   ├── Credits.tsx            # Credit management
│   ├── Discovery.tsx          # System explorer
│   └── Settings.tsx           # User preferences
├── stores/                    # Zustand state management
├── hooks/
│   ├── useMCPTools.ts         # React Query hooks
│   └── useKeyboardShortcuts.ts # ⭐ NEW!
├── lib/                       # API client
└── types/                     # TypeScript definitions
```

## Credit Costs

| Tool | Base Cost | Notes |
|------|-----------|-------|
| Get Document | 1 | +1 per 10 records above 20 |
| Get List | 1 | +1 per 10 records above 20 |
| Search Documents | 2 | +1 per 10 results above 20 |
| Create Document | 3 | Fixed cost |
| Update Document | 2 | Fixed cost |
| Delete Document | 2 | Destructive operation |
| Get Dashboard Data | 2 | Fixed cost |
| Execute Report | 5 | +1 per 3 filters |
| Export Data | 5 | +1 per 10 records above 20 |
| Bulk Create | 3 per record | Create multiple documents ⭐ NEW! |
| Bulk Update | 2 per record | Update multiple documents ⭐ NEW! |
| Bulk Delete | 2 per record | Delete multiple documents ⭐ NEW! |
| CSV Import | 3 per record | Import from CSV ⭐ NEW! |

**Note:** AI API costs (OpenAI/Anthropic) are separate and billed by those providers.

## Configuration

### MCP Settings DocType

Configure all features via **Frappe Desk → MCP Settings**:

#### AI Integration
- **Enable AI-Powered NLP**: Toggle AI features on/off
- **AI Provider**: Choose OpenAI, Anthropic, or Local (basic NLP)
- **OpenAI API Key**: Your OpenAI API key (get from [platform.openai.com](https://platform.openai.com))
- **OpenAI Model**: 
  - `gpt-4o` - Most capable multimodal model
  - `gpt-4o-mini` - Fast and cost-effective (recommended)
  - `o1-preview` - Advanced reasoning model
  - `o1-mini` - Reasoning model (affordable)
- **Anthropic API Key**: Your Anthropic API key (get from [console.anthropic.com](https://console.anthropic.com))
- **Anthropic Model**:
  - `claude-3-5-sonnet-20241022` - Most capable (latest)
  - `claude-3-5-haiku-20241022` - Fast and affordable (recommended)
  - `claude-3-opus-20240229` - Powerful legacy model

#### Features
- **Enable Bulk Operations**: Allow bulk create/update/delete
- **Enable Keyboard Shortcuts**: Global keyboard shortcuts
- **Max Bulk Records**: Maximum records per bulk operation (default: 100)
- **Default List Limit**: Default number of records in lists (default: 20)

#### UI Preferences
- **Default Mode**: Simple or Advanced
- **Enable Confetti**: Success animations
- **Enable Animations**: UI animations
- **Default Theme**: Light, Dark, or System
- **Compact Mode**: Dense UI layout

### Custom Tools

Add custom tools by extending the MCP server:

```python
# In your custom app
from mcp_ui.mcp_server.mcp import mcp

@mcp.tool()
def custom_tool(param1: str, param2: int):
    """Custom tool description"""
    # Your logic here
    return {"result": "success"}
```

### Credit Package Customization

Modify default packages in `mcp_ui/fixtures/credit_packages.py`

### API Endpoints

All APIs are whitelisted and accessible at:
- `/api/method/mcp_ui.api.tools.*`
- `/api/method/mcp_ui.api.credits.*`
- `/api/method/mcp_ui.api.discovery.*`
- `/api/method/mcp_ui.api.form_builder.*` ⭐ NEW!
- `/api/method/mcp_ui.api.nlp_processor.*` ⭐ NEW!
- `/api/method/mcp_ui.api.ai_nlp.*` ⭐ NEW!
- `/api/method/mcp_ui.api.bulk_operations.*` ⭐ NEW!

## Development

### Frontend Development

```bash
cd apps/mcp_ui/mcp
yarn dev  # Start development server
```

### Backend Development

```bash
bench --site your-site console
>>> from mcp_ui.api import credits
>>> credits.get_balance()
```

## AI Integration Details

### How OpenAI Function Calling Works

When AI is enabled with OpenAI:

1. **Frontend sends user query** to `/api/method/mcp_ui.api.ai_nlp.parse_with_ai`
2. **Backend prepares function definitions**:
   ```python
   tools = [
       {
           "type": "function",
           "function": {
               "name": "create_document",
               "description": "Create a new document/record...",
               "parameters": {
                   "type": "object",
                   "properties": {
                       "doctype": {
                           "type": "string",
                           "enum": ["Customer", "Item", ...],  # All available DocTypes
                       }
                   }
               }
           }
       },
       # ... more tools
   ]
   ```
3. **Call OpenAI with tools**:
   ```python
   response = client.chat.completions.create(
       model="gpt-4o-mini",
       messages=[{"role": "user", "content": query}],
       tools=tools,
       tool_choice="auto"
   )
   ```
4. **OpenAI returns function call**:
   ```json
   {
       "tool_calls": [{
           "function": {
               "name": "create_document",
               "arguments": "{\"doctype\": \"Customer\"}"
           }
       }]
   }
   ```
5. **Frontend receives structured response** and shows appropriate UI (form, confirmation, etc.)

### How Anthropic Tool Use Works

Similar to OpenAI but uses Anthropic's tool format:

1. **Frontend sends query** (same endpoint)
2. **Backend prepares Anthropic tools**:
   ```python
   tools = [
       {
           "name": "create_document",
           "description": "Create a new document/record...",
           "input_schema": {
               "type": "object",
               "properties": {
                   "doctype": {
                       "type": "string",
                       "enum": ["Customer", "Item", ...]
                   }
               }
           }
       }
   ]
   ```
3. **Call Anthropic with tools**:
   ```python
   message = client.messages.create(
       model="claude-3-haiku-20240307",
       messages=[{"role": "user", "content": query}],
       tools=tools
   )
   ```
4. **Claude returns tool use**:
   ```python
   for content in message.content:
       if content.type == "tool_use":
           tool_name = content.name  # "create_document"
           tool_input = content.input  # {"doctype": "Customer"}
   ```
5. **Frontend shows smart form** based on the tool and params

### Why This Approach?

✅ **More Accurate**: AI natively understands tool schemas  
✅ **Type Safe**: DocTypes validated as enums  
✅ **Robust**: Structured output guaranteed  
✅ **Flexible**: Easy to add new tools  
✅ **Cost Effective**: gpt-4o-mini is very cheap  

## Troubleshooting

### Frontend not loading
1. Check if `mcp_ui/public/mcp/index.html` exists
2. Rebuild frontend: `cd apps/mcp_ui/mcp && yarn build`
3. Clear cache: `bench --site your-site clear-cache`

### AI features not working
1. **Check API keys** in MCP Settings
2. **Verify packages installed**:
   ```bash
   pip list | grep openai    # For OpenAI
   pip list | grep anthropic # For Anthropic
   ```
3. **Test internet connectivity** (AI APIs are external)
4. **Check browser console** for errors
5. **Review Error Log** in Frappe for API errors

### Credits not deducting
1. Check if MCP User Credits doc exists for user
2. Verify API whitelist in hooks.py
3. Check browser console for errors

### Tools not executing
1. Verify frappe-mcp is installed: `pip list | grep frappe-mcp`
2. Check tool registration in backend
3. Review usage logs for error messages

### Keyboard shortcuts not working
1. Enable in MCP Settings → Features → Enable Keyboard Shortcuts
2. Clear browser cache (Cmd+Shift+R)
3. Check if you're focused in an input field (shortcuts disabled there)

## License

MIT

## Credits

Built with:
- [Frappe Framework](https://frappeframework.com)
- [frappe-mcp](https://pypi.org/project/frappe-mcp/)
- [React](https://react.dev)
- [shadcn/ui](https://ui.shadcn.com)
- [Tailwind CSS](https://tailwindcss.com)

## Support

For issues and feature requests, please create an issue on GitHub.
