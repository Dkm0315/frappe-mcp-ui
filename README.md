# MCP UI — AI Business Automation for Frappe/ERPNext

An AI engine that sits on top of your entire Frappe/ERPNext system. Users interact via **web chat** or **Telegram** and the AI executes real business processes — not generic advice.

**What it does:**
- Runs full document chains: Quotation → Sales Order → Delivery Note → Sales Invoice
- Bulk creates hundreds of records from an Excel upload
- Runs reports and analyzes data with actual insights
- Manages workflows, approvals, and document submissions
- Works across every installed Frappe app — Helpdesk, CRM, ERPNext, custom apps

**Two channels, same brain:**
- **Web Chat** (`/mcp` → Chat page) — streaming responses via Vercel AI SDK
- **Telegram Bot** (via OpenClaw) — same 29 tools, same permissions, auto-managed by Frappe scheduler

## Install

```bash
bench get-app https://github.com/Dkm0315/frappe-mcp-ui --branch develop
bench --site your-site install-app mcp_ui
bench --site your-site migrate
```

The install automatically sets up OpenClaw npm packages. If Node.js isn't available, you can run the setup later from MCP Settings.

## Configure

Go to **MCP Settings** in Frappe Desk:

**1. AI Provider**
- Pick a provider: OpenAI, Anthropic, Google, or Ollama (local)
- Set the model (e.g. `gpt-4o-mini`, `claude-sonnet-4-6`, `qwen3:14b`)
- Enter your API key (not needed for Ollama)

**2. Telegram Bot** (optional)
- Create a bot via [@BotFather](https://t.me/BotFather) on Telegram
- Paste the bot token in MCP Settings
- Map Telegram usernames to Frappe users (controls permissions)
- Enable "OpenClaw Enabled" checkbox

**3. Access Control**
- Select which DocTypes the AI can access per module
- Even if a user has Frappe permission, the AI won't touch DocTypes not on this list

**4. Generate Config & Start**
- Click **Setup OpenClaw** — installs packages, generates config, starts the gateway
- The Frappe scheduler keeps the gateway alive automatically (restarts if it crashes)

## How It Works

The AI has **29 tools** covering every business operation:

| Category | Tools |
|----------|-------|
| CRUD | get_list, get_document, create_document, update_document, delete_document, search_documents |
| Lifecycle | submit_document, cancel_document, amend_document, make_mapped_document |
| Bulk | bulk_create, bulk_update, bulk_delete |
| Excel | parse_excel, import_from_excel, export_to_excel |
| Reports | run_report, get_dashboard_data, get_count, analyze_data |
| Process | get_linked_documents, get_workflow_info, get_pending_approvals, get_doctype_meta |
| Other | execute_automation_chain, web_search, get_module_context, get_form_guidance, get_process_chain |

Every tool call runs through `frappe.has_permission()` as the current user. A sales rep can't see manufacturing BOMs. An HR manager can't see another branch's data. Frappe's RBAC is enforced automatically.

## Architecture

```
mcp_ui/
├── ai/
│   ├── engine.py          # Multi-step streaming chat (up to 25 tool rounds)
│   ├── tools.py           # 29 business automation tools
│   ├── stream.py          # Vercel AI SDK Data Stream Protocol
│   └── providers.py       # LLM provider config via litellm
├── openclaw/
│   ├── server.py          # MCP stdio server (what OpenClaw spawns)
│   └── manager.py         # Process manager (start/stop/auto-restart via scheduler)
├── api/
│   ├── ai_chat.py         # SSE streaming endpoint for web chat
│   └── openclaw.py        # Config generator, SOUL.md generator, gateway control
└── mcp/src/
    ├── pages/Chat.tsx     # Web chat UI with useChat()
    └── components/chat/   # Rich result renderers (DataTable, ProcessChain, etc.)
```

## Requirements

- Frappe Framework v15+
- Python 3.10+
- Node.js v20+ (for OpenClaw gateway)
- An LLM provider: OpenAI API key, Anthropic API key, or local Ollama

## License

MIT
