import { spawnSync } from "node:child_process";

import { Type } from "@sinclair/typebox";
import { definePluginEntry } from "openclaw/plugin-sdk/plugin-entry";


function toTextResult(payload) {
	return {
		content: [
			{
				type: "text",
				text: JSON.stringify(payload, null, 2),
			},
		],
	};
}


function compactPlanPayload(payload) {
	if (!payload || typeof payload !== "object") {
		return payload;
	}

	const resolution = payload.resolution && typeof payload.resolution === "object"
		? {
			success: payload.resolution.success,
			site: payload.resolution.site,
			frappe_user: payload.resolution.frappe_user,
			full_name: payload.resolution.full_name,
			roles: payload.resolution.roles,
			matched_on: payload.resolution.matched_on,
		}
		: payload.resolution;

	const relatedReports = Array.isArray(payload.related_reports)
		? payload.related_reports.slice(0, 6)
		: [];
	const candidateActions = Array.isArray(payload.candidate_actions)
		? payload.candidate_actions.slice(0, 6).map((action) => ({
			name: action.name,
			category: action.category,
			write: action.write,
			mode_required: action.mode_required,
			execution_path: action.execution_path,
			reason: action.reason,
		}))
		: [];

	return {
		success: payload.success,
		status: payload.status,
		request: payload.request,
		scope: {
			doctype: payload.top_doctype || "",
			report: payload.top_report || "",
			related_reports: relatedReports,
			answer_constraints: payload.answer_constraints || {},
		},
		resolution,
		session_mode: payload.session_mode,
		intents: payload.intents || [],
		execution_path: payload.execution_path,
		permission_summary: payload.permission_summary || {},
		missing_inputs: payload.missing_inputs || [],
		confirmation_required: Boolean(payload.confirmation_required),
		plan_steps: payload.plan_steps || [],
		create_plan: payload.create_plan || null,
		candidate_actions: candidateActions,
	};
}


function normalizeString(value) {
	return typeof value === "string" ? value : value == null ? "" : String(value);
}


function inferChannel(ctx) {
	return normalizeString(ctx.messageChannel || ctx.deliveryContext?.channel);
}


function buildSessionContext(ctx, pluginConfig) {
	const delivery = ctx.deliveryContext || {};
	const externalId = normalizeString(ctx.requesterSenderId || "");
	const externalUsername = normalizeString(
		ctx.requesterSenderUsername ||
		ctx.SenderUsername ||
		ctx.senderUsername ||
		delivery.senderUsername ||
		delivery.username ||
		"",
	).replace(/^@+/, "");
	const senderName = normalizeString(
		ctx.SenderName ||
		ctx.requesterSenderName ||
		ctx.senderName ||
		delivery.senderName ||
		"",
	);
	return {
		site: normalizeString(pluginConfig.site),
		channel: inferChannel(ctx),
		external_id: externalId || normalizeString(ctx.sessionKey),
		external_username: externalUsername,
		sender_name: senderName,
		chat_id: normalizeString(delivery.to),
		thread_id: normalizeString(delivery.threadId),
		session_key: normalizeString(ctx.sessionKey),
		session_id: normalizeString(ctx.sessionId),
		agent_id: normalizeString(ctx.agentId),
	};
}


function runBridge(pluginConfig, operation, payload = {}) {
	const pythonPath = normalizeString(pluginConfig.pythonPath);
	if (!pythonPath) {
		return { success: false, error: "Plugin config is missing pythonPath." };
	}

	const env = {
		...process.env,
		FRAPPE_BENCH: normalizeString(pluginConfig.benchPath),
		FRAPPE_SITE: normalizeString(pluginConfig.site),
		FRAPPE_BOOT_USER: normalizeString(pluginConfig.bootUser || "Administrator"),
	};

	const result = spawnSync(
		pythonPath,
		["-m", normalizeString(pluginConfig.bridgeModule || "mcp_ui.openclaw.plugin_bridge"), operation],
		{
			cwd: normalizeString(pluginConfig.benchPath) || process.cwd(),
			env,
			input: JSON.stringify(payload),
			encoding: "utf8",
		},
	);

	if (result.error) {
		return {
			success: false,
			error: `Bridge process failed: ${result.error.message}`,
		};
	}

	const stdout = normalizeString(result.stdout).trim();
	if (!stdout) {
		return {
			success: false,
			error: normalizeString(result.stderr) || `Bridge process exited with code ${result.status ?? "unknown"}`,
		};
	}

	try {
		return JSON.parse(stdout);
	} catch (error) {
		return {
			success: false,
			error: `Bridge returned invalid JSON: ${error instanceof Error ? error.message : String(error)}`,
			stdout,
			stderr: normalizeString(result.stderr),
		};
	}
}


function createManifestTool(pluginConfig, ctx) {
	return {
		name: "frappe_get_site_manifest",
		description: "Fetch a concise Frappe site manifest summary. Use this for counts, app/module overviews, workflows, reports, and targeted sections. Request full detail only when necessary.",
		parameters: Type.Object({
			refresh: Type.Optional(Type.Boolean({ description: "Force a fresh manifest rebuild before returning it." })),
			detail_level: Type.Optional(Type.String({ description: "Use 'summary' by default. Use 'full' only when you truly need the entire manifest." })),
			sections: Type.Optional(Type.Array(Type.String(), { description: "Optional sections such as apps, modules, doctypes, workflows, reports, customizations, nextai." })),
			limit_per_section: Type.Optional(Type.Number({ description: "Max items per section in summary mode." })),
		}),
		async execute(_toolCallId, params) {
			return toTextResult(
				runBridge(pluginConfig, "get_site_manifest", {
					site: pluginConfig.site,
					refresh: Boolean(params?.refresh),
					detail_level: params?.detail_level || "summary",
					sections: params?.sections || undefined,
					limit_per_section: params?.limit_per_section || 10,
					session_context: buildSessionContext(ctx, pluginConfig),
				}),
			);
		},
	};
}


function createContextSearchTool(pluginConfig, ctx) {
	return {
		name: "frappe_search_site_context",
		description: "Search apps, modules, doctypes, workflows, reports, pages, scripts, custom fields, and property setters from natural language. Use this first for module discovery and ambiguous ERP questions. This tool returns schema and context matches only, not actual business records or report rows.",
		parameters: Type.Object({
			query: Type.String({ description: "Natural-language search text, for example 'candidate onboarding workflow' or 'customer invoice report'." }),
			sections: Type.Optional(Type.Array(Type.String(), { description: "Optional sections to search, such as doctypes, reports, workflows, custom_fields, scripts." })),
			limit: Type.Optional(Type.Number({ description: "Max matches to return." })),
		}),
		async execute(_toolCallId, params) {
			return toTextResult(
				runBridge(pluginConfig, "search_site_context", {
					site: pluginConfig.site,
					query: params?.query || "",
					sections: params?.sections || undefined,
					limit: params?.limit || 12,
					session_context: buildSessionContext(ctx, pluginConfig),
				}),
			);
		},
	};
}


function createTypedRetrievalTool(pluginConfig, ctx) {
	return {
		name: "frappe_retrieve_site_context",
		description: "Run typed lexical retrieval across doctypes, reports, workflows, UI surfaces, scripts, hooks, custom fields, property setters, NextAI funnels, and actions. Use this for broad ERP questions where you need grouped candidates, not a flat schema search.",
		parameters: Type.Object({
			query: Type.String({ description: "Natural-language retrieval query." }),
			limit: Type.Optional(Type.Number({ description: "Max results per group." })),
		}),
		async execute(_toolCallId, params) {
			return toTextResult(
				runBridge(pluginConfig, "retrieve_site_context", {
					site: pluginConfig.site,
					query: params?.query || "",
					limit: params?.limit || 5,
					session_context: buildSessionContext(ctx, pluginConfig),
				}),
			);
		},
	};
}


function createRefreshTool(pluginConfig, ctx) {
	return {
		name: "frappe_refresh_site_context",
		description: "Refresh the generated Frappe context, manifest, and site-local skills after app updates, migrations, workflow changes, or customization changes.",
		parameters: Type.Object({
			reason: Type.Optional(Type.String({ description: "Why the refresh is being triggered." })),
		}),
		async execute(_toolCallId, params) {
			return toTextResult(
				runBridge(pluginConfig, "refresh_site_context", {
					site: pluginConfig.site,
					reason: params?.reason || "manual",
					session_context: buildSessionContext(ctx, pluginConfig),
				}),
			);
		},
	};
}


function createChangeSummaryTool(pluginConfig, ctx) {
	return {
		name: "frappe_get_change_summary",
		description: "Summarize what changed in the current Frappe site or module, using manifest diffs and refresh history.",
		parameters: Type.Object({
			since_hash_or_timestamp: Type.Optional(
				Type.String({ description: "Optional manifest hash or timestamp to diff against." }),
			),
		}),
		async execute(_toolCallId, params) {
			return toTextResult(
				runBridge(pluginConfig, "get_change_summary", {
					site: pluginConfig.site,
					since_hash_or_timestamp: params?.since_hash_or_timestamp || "",
					session_context: buildSessionContext(ctx, pluginConfig),
				}),
			);
		},
	};
}


function createPlannerTool(pluginConfig, ctx) {
	return {
		name: "frappe_plan_request",
		description: "Plan a vague, multi-step, write-heavy, or analytical ERP request before execution. It returns detected intents, typed retrieval results, permission hints, candidate actions, missing inputs, and whether confirmation or admin mode is required.",
		parameters: Type.Object({
			request: Type.String({ description: "The user's natural-language request." }),
			draft: Type.Optional(Type.Object({}, { additionalProperties: true, description: "Optional structured details already collected from the user." })),
		}),
		async execute(_toolCallId, params) {
			return toTextResult(
				compactPlanPayload(runBridge(pluginConfig, "plan_request", {
					request: params?.request || "",
					draft: params?.draft || {},
					session_context: buildSessionContext(ctx, pluginConfig),
				})),
			);
		},
	};
}


function createActionCatalogTool(pluginConfig, ctx) {
	return {
		name: "frappe_get_action_catalog",
		description: "List available Frappe actions in compact form. Use this when you need the exact action name for real data access or writes. For record listing/search use actions like get_list or get_document. For report rows use run_report.",
		parameters: Type.Object({
			query: Type.Optional(Type.String({ description: "Optional substring filter for action names." })),
			category: Type.Optional(Type.String({ description: "Optional category filter, for example workflow, ide, discovery, form, or tool." })),
			write_only: Type.Optional(Type.Boolean({ description: "Return only write-capable actions." })),
			destructive_only: Type.Optional(Type.Boolean({ description: "Return only destructive actions." })),
			limit: Type.Optional(Type.Number({ description: "Max actions to return." })),
			verbose: Type.Optional(Type.Boolean({ description: "Return the full filtered list. Leave false for compact output." })),
		}),
		async execute(_toolCallId, params) {
			return toTextResult(
				runBridge(pluginConfig, "get_action_catalog", {
					site: pluginConfig.site,
					query: params?.query || "",
					category: params?.category || "",
					write_only: Boolean(params?.write_only),
					destructive_only: Boolean(params?.destructive_only),
					limit: params?.limit || 12,
					verbose: Boolean(params?.verbose),
					session_context: buildSessionContext(ctx, pluginConfig),
				}),
			);
		},
	};
}


function createSessionModeTool(pluginConfig, ctx, write = false) {
	return {
		name: write ? "frappe_set_session_mode" : "frappe_get_session_mode",
		description: write
			? "Set the session mode to normal or admin. Only use this when the user explicitly asks to enter or exit admin mode."
			: "Return the current session mode for this conversation.",
		parameters: write
			? Type.Object({
				mode: Type.String({ description: "normal or admin" }),
			})
			: Type.Object({}),
		async execute(_toolCallId, params) {
			return toTextResult(
				runBridge(pluginConfig, write ? "set_session_mode" : "get_session_mode", {
					mode: params?.mode || "normal",
					session_context: buildSessionContext(ctx, pluginConfig),
				}),
			);
		},
	};
}


function createWhoAmITool(pluginConfig, ctx) {
	return {
		name: "frappe_whoami",
		description: "Resolve the current OpenClaw sender to the mapped Frappe user and roles for this site.",
		parameters: Type.Object({}),
		async execute() {
			return toTextResult(runBridge(pluginConfig, "resolve_identity", buildSessionContext(ctx, pluginConfig)));
		},
	};
}


function createExecuteTool(pluginConfig, ctx, validateOnly = false) {
	return {
		name: validateOnly ? "frappe_validate_action" : "frappe_execute_action",
		description: validateOnly
			? "Validate a Frappe action as the mapped ERP user without committing the change. Use this before writes when you want to check permissions, schema, or validation."
			: "Execute a Frappe action as the mapped ERP user. Use this after planning. Low-level CRUD actions are primitives; prefer planner-selected capabilities, workflows, reports, and guided create/update flows for vague end-user requests.",
		parameters: Type.Object({
			action: Type.String({ description: "Action name from frappe_get_action_catalog, for example create_document or workflow.create_funnel." }),
			args: Type.Optional(Type.Object({}, { additionalProperties: true, description: "Action arguments as a JSON object." })),
			confirmed: Type.Optional(Type.Boolean({ description: "Set true only after the user explicitly confirms the write." })),
			confirmation_note: Type.Optional(Type.String({ description: "Optional short note describing what the user confirmed." })),
		}),
		async execute(_toolCallId, params) {
			return toTextResult(
				runBridge(pluginConfig, "execute_as_user", {
					session_context: buildSessionContext(ctx, pluginConfig),
					action: params?.action || "",
					args: params?.args || {},
					validate_only: validateOnly,
					confirmed: Boolean(params?.confirmed),
					confirmation_note: params?.confirmation_note || "",
				}),
			);
		},
	};
}


function createPrepareCreateTool(pluginConfig, ctx) {
	return {
		name: "frappe_prepare_create_record",
		description: "Prepare a record-creation flow for a vague user request. Use this before creating documents when the user has not supplied enough fields. It resolves the target DocType, checks create permission, inspects the live form, and returns the exact follow-up questions to ask.",
		parameters: Type.Object({
			request: Type.String({ description: "The user's natural-language create request, for example 'create a leave request'." }),
			doctype: Type.Optional(Type.String({ description: "Optional explicit DocType if already known." })),
			draft: Type.Optional(Type.Object({}, { additionalProperties: true, description: "Optional partial field values already collected from the user." })),
		}),
		async execute(_toolCallId, params) {
			return toTextResult(
				runBridge(pluginConfig, "prepare_create_record", {
					session_context: buildSessionContext(ctx, pluginConfig),
					request: params?.request || "",
					doctype: params?.doctype || "",
					draft: params?.draft || {},
				}),
			);
		},
	};
}


export default definePluginEntry({
	id: "frappe-federated",
	name: "Frappe Federated",
	description: "Session-aware, rights-aware bridge from OpenClaw into a colocated Frappe site.",
	register(api) {
		const pluginConfig = api.pluginConfig || {};

		api.registerTool((ctx) => createWhoAmITool(pluginConfig, ctx), { name: "frappe_whoami" });
		api.registerTool((ctx) => createSessionModeTool(pluginConfig, ctx, false), { name: "frappe_get_session_mode" });
		api.registerTool((ctx) => createSessionModeTool(pluginConfig, ctx, true), { name: "frappe_set_session_mode" });
		api.registerTool((ctx) => createManifestTool(pluginConfig, ctx), { name: "frappe_get_site_manifest" });
		api.registerTool((ctx) => createContextSearchTool(pluginConfig, ctx), { name: "frappe_search_site_context" });
		api.registerTool((ctx) => createTypedRetrievalTool(pluginConfig, ctx), { name: "frappe_retrieve_site_context" });
		api.registerTool((ctx) => createPlannerTool(pluginConfig, ctx), { name: "frappe_plan_request" });
		api.registerTool((ctx) => createRefreshTool(pluginConfig, ctx), { name: "frappe_refresh_site_context" });
		api.registerTool((ctx) => createChangeSummaryTool(pluginConfig, ctx), { name: "frappe_get_change_summary" });
		api.registerTool((ctx) => createActionCatalogTool(pluginConfig, ctx), { name: "frappe_get_action_catalog" });
		api.registerTool((ctx) => createPrepareCreateTool(pluginConfig, ctx), { name: "frappe_prepare_create_record" });
		api.registerTool((ctx) => createExecuteTool(pluginConfig, ctx, false), { name: "frappe_execute_action" });
		api.registerTool((ctx) => createExecuteTool(pluginConfig, ctx, true), { name: "frappe_validate_action" });
	},
});
