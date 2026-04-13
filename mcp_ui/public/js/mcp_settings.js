frappe.ui.form.on("MCP Settings", {
	refresh(frm) {
		add_openclaw_buttons(frm);
	},
});

function add_openclaw_buttons(frm) {
	frm.add_custom_button("Generate OpenClaw Config", async () => {
		const result = await frappe.call({
			method: "mcp_ui.api.openclaw.generate_config",
		});
		const message = result.message || {};
		frappe.msgprint({
			title: "OpenClaw Config Generated",
			indicator: "green",
			message: `
				<div><strong>Config:</strong> ${frappe.utils.escape_html(message.config_path || "")}</div>
				<div><strong>Runtime Root:</strong> ${frappe.utils.escape_html(message.runtime_root || "")}</div>
			`,
		});
		frm.reload_doc();
	});

	frm.add_custom_button("Restart Gateway", async () => {
		const result = await frappe.call({
			method: "mcp_ui.api.openclaw.restart_gateway",
		});
		const message = result.message || {};
		if (!message.success) {
			frappe.msgprint({
				title: "Gateway Restart Failed",
				indicator: "red",
				message: frappe.utils.escape_html(message.error || "Unknown error"),
			});
			return;
		}
		frappe.show_alert({ message: `Gateway restarted (PID ${message.pid})`, indicator: "green" });
		frm.reload_doc();
	});

	frm.add_custom_button("Setup Telegram User", () => {
		const dialog = new frappe.ui.Dialog({
			title: "Setup Telegram User",
			fields: [
				{
					fieldname: "frappe_user",
					fieldtype: "Data",
					label: "Frappe User Email",
					reqd: 1,
				},
				{
					fieldname: "full_name",
					fieldtype: "Data",
					label: "Full Name",
				},
				{
					fieldname: "telegram_username",
					fieldtype: "Data",
					label: "Telegram Username",
					description: "Without @",
				},
				{
					fieldname: "send_welcome_email",
					fieldtype: "Check",
					label: "Send Welcome Email",
					default: 0,
				},
			],
			primary_action_label: "Create User + Mapping",
			primary_action: async (values) => {
				if (!values.telegram_username) {
					frappe.msgprint("Provide a Telegram username.");
					return;
				}

				dialog.disable_primary_action();
				try {
					const result = await frappe.call({
						method: "mcp_ui.api.openclaw.provision_telegram_user",
						args: values,
					});
					const message = result.message || {};
					const warnings = (message.warnings || [])
						.map((warning) => `<li>${frappe.utils.escape_html(warning)}</li>`)
						.join("");

					frappe.msgprint({
						title: "Telegram Provisioning Complete",
						indicator: warnings ? "orange" : "green",
						message: `
							<div><strong>User:</strong> ${frappe.utils.escape_html(message.user?.name || "")}</div>
							<div><strong>Identity Mapping:</strong> ${frappe.utils.escape_html(message.identity_mapping?.name || "")}</div>
							<div><strong>Config:</strong> ${frappe.utils.escape_html(message.config_path || "")}</div>
							${warnings ? `<div style="margin-top: 8px;"><strong>Warnings</strong><ul>${warnings}</ul></div>` : ""}
						`,
					});
					dialog.hide();
					frm.reload_doc();
				} finally {
					dialog.enable_primary_action();
				}
			},
		});

		dialog.show();
	});
}
