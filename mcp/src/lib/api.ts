/**
 * Frappe API Client
 * Handles all API calls to Frappe backend
 */

interface FrappeResponse<T = any> {
  message: T;
}

class FrappeAPI {
  private baseURL: string;

  constructor() {
    this.baseURL = window.location.origin;
  }

  /**
   * Get CSRF token from window
   */
  private getCSRFToken(): string {
    return window.csrf_token || window.frappe?.csrf_token || '';
  }

  /**
   * Make API call to Frappe
   */
  async call<T = any>(method: string, args: Record<string, any> = {}): Promise<T> {
    const url = `${this.baseURL}/api/method/${method}`;
    
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Frappe-CSRF-Token': this.getCSRFToken(),
      },
      credentials: 'include',
      body: JSON.stringify(args),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || error.exc || 'API call failed');
    }

    const data: FrappeResponse<T> = await response.json();
    return data.message;
  }

  /**
   * Get available MCP tools
   */
  async getTools() {
    return this.call('mcp_ui.api.tools.get_available_tools');
  }

  /**
   * Execute an MCP tool
   */
  async executeTool(toolName: string, params: Record<string, any>) {
    return this.call('mcp_ui.api.tools.execute_tool', {
      tool_name: toolName,
      params: JSON.stringify(params),
    });
  }

  /**
   * Get tool schema
   */
  async getToolSchema(toolName: string) {
    return this.call('mcp_ui.api.tools.get_tool_schema', {
      tool_name: toolName,
    });
  }

  /**
   * Get credit balance
   */
  async getCreditBalance() {
    return this.call('mcp_ui.api.credits.get_balance');
  }

  /**
   * Get usage history
   */
  async getUsageHistory(limit = 50) {
    return this.call('mcp_ui.api.credits.get_usage_history', { limit });
  }

  /**
   * Get available credit packages
   */
  async getAvailablePackages() {
    return this.call('mcp_ui.api.credits.get_available_packages');
  }

  /**
   * Purchase credit package
   */
  async purchaseCredits(packageName: string) {
    return this.call('mcp_ui.api.credits.purchase_credits', {
      package_name: packageName,
    });
  }

  /**
   * Get installed apps
   */
  async getInstalledApps() {
    return this.call('mcp_ui.api.discovery.get_installed_apps');
  }

  /**
   * Get DocTypes
   */
  async getDocTypes(app?: string, module?: string) {
    return this.call('mcp_ui.api.discovery.get_doctypes', { app, module });
  }

  /**
   * Get custom fields
   */
  async getCustomFields(doctype?: string) {
    return this.call('mcp_ui.api.discovery.get_custom_fields', { doctype });
  }

  /**
   * Get workflows
   */
  async getWorkflows() {
    return this.call('mcp_ui.api.discovery.get_workflows');
  }

  /**
   * Get DocType metadata
   */
  async getDocTypeMeta(doctype: string) {
    return this.call('mcp_ui.api.discovery.get_doctype_meta', { doctype });
  }

  /**
   * Get system statistics
   */
  async getSystemStats() {
    return this.call('mcp_ui.api.discovery.get_system_stats');
  }

  /**
   * Get DocType form fields (user-friendly)
   */
  async getDocTypeFormFields(doctype: string) {
    return this.call('mcp_ui.api.form_builder.get_doctype_form_fields', { doctype });
  }

  /**
   * Search link field values (autocomplete)
   */
  async searchLinkField(doctype: string, searchTerm: string, limit = 20) {
    return this.call('mcp_ui.api.form_builder.search_link_field', {
      doctype,
      search_term: searchTerm,
      limit,
    });
  }

  /**
   * Get quick create templates
   */
  async getQuickCreateTemplates() {
    return this.call('mcp_ui.api.form_builder.get_quick_create_templates');
  }

  /**
   * Parse natural language query
   */
  async parseNaturalLanguage(query: string) {
    return this.call('mcp_ui.api.ai_nlp.parse_with_ai', { query });
  }

  /**
   * Get system health and configuration status
   */
  async getSystemHealth() {
    return this.call('mcp_ui.utils.app_checker.get_system_health');
  }

  /**
   * Get DocTypes grouped by module
   */
  async getDocTypesByModule(app?: string) {
    return this.call('mcp_ui.api.discovery.get_doctypes_by_module', { app });
  }

  // ===== Workflow Integration APIs =====

  /**
   * Get available Funnel workflows
   */
  async getFunnelWorkflows(category?: string) {
    return this.call('mcp_ui.api.workflow_integration.get_workflows', { category });
  }

  /**
   * Trigger a Funnel workflow
   */
  async triggerWorkflow(funnelName: string, variables?: Record<string, any>) {
    return this.call('mcp_ui.api.workflow_integration.trigger_workflow', {
      funnel_name: funnelName,
      variables: variables ? JSON.stringify(variables) : undefined,
    });
  }

  /**
   * Get workflow execution status
   */
  async getWorkflowStatus(workflowId: string) {
    return this.call('mcp_ui.api.workflow_integration.get_workflow_status', {
      workflow_id: workflowId,
    });
  }

  /**
   * Get workflow definition
   */
  async getWorkflowDefinition(funnelName: string) {
    return this.call('mcp_ui.api.workflow_integration.get_workflow_definition', {
      funnel_name: funnelName,
    });
  }

  /**
   * Get workflow builder URL for embedding
   */
  async getBuilderUrl(funnelName?: string) {
    return this.call('mcp_ui.api.workflow_integration.get_builder_url', {
      funnel_name: funnelName,
    });
  }

  // ===== Bulk Operations APIs =====

  /**
   * Bulk create documents (standard or AI-powered)
   */
  async bulkCreateDocuments(
    doctype: string,
    options: {
      records?: any[];
      useAI?: boolean;
      aiTemplate?: {
        count: number;
        type?: string;
        edge_cases?: boolean;
        base_data?: Record<string, any>;
      };
    }
  ) {
    return this.call('mcp_ui.api.bulk_operations.bulk_create_documents', {
      doctype,
      records: options.records ? JSON.stringify(options.records) : undefined,
      use_ai_generation: options.useAI || false,
      ai_template: options.aiTemplate ? JSON.stringify(options.aiTemplate) : undefined,
    });
  }

  /**
   * Bulk update documents
   */
  async bulkUpdateDocuments(
    doctype: string,
    filters: Record<string, any>,
    updateData: Record<string, any>
  ) {
    return this.call('mcp_ui.api.bulk_operations.bulk_update_documents', {
      doctype,
      filters: JSON.stringify(filters),
      update_data: JSON.stringify(updateData),
    });
  }

  /**
   * Bulk delete documents
   */
  async bulkDeleteDocuments(doctype: string, filters: Record<string, any>) {
    return this.call('mcp_ui.api.bulk_operations.bulk_delete_documents', {
      doctype,
      filters: JSON.stringify(filters),
    });
  }

  // ===== IDE APIs =====

  async getCapabilities() {
    return this.call('mcp_ui.api.ide.get_capabilities');
  }

  // Client Scripts
  async getClientScripts(doctype?: string) {
    return this.call('mcp_ui.api.ide.get_client_scripts', { doctype });
  }

  async getClientScript(name: string) {
    return this.call('mcp_ui.api.ide.get_client_script', { name });
  }

  async saveClientScript(data: {
    name?: string; dt?: string; view?: string;
    enabled?: number; script?: string; module?: string;
  }) {
    return this.call('mcp_ui.api.ide.save_client_script', data);
  }

  async deleteClientScript(name: string) {
    return this.call('mcp_ui.api.ide.delete_client_script', { name });
  }

  // Server Scripts
  async getServerScripts(doctype?: string, scriptType?: string) {
    return this.call('mcp_ui.api.ide.get_server_scripts', {
      doctype, script_type: scriptType,
    });
  }

  async getServerScript(name: string) {
    return this.call('mcp_ui.api.ide.get_server_script', { name });
  }

  async saveServerScript(data: {
    name?: string; script_type?: string; reference_doctype?: string;
    doctype_event?: string; api_method?: string; script?: string;
    disabled?: number; event_frequency?: string; cron_format?: string;
    allow_guest?: number; module?: string;
  }) {
    return this.call('mcp_ui.api.ide.save_server_script', data);
  }

  async deleteServerScript(name: string) {
    return this.call('mcp_ui.api.ide.delete_server_script', { name });
  }

  // Workflows
  async getFrappeWorkflows() {
    return this.call('mcp_ui.api.ide.get_frappe_workflows');
  }

  async saveFrappeWorkflow(data: {
    workflow_name: string; document_type: string; is_active?: number;
    states?: any[]; transitions?: any[];
  }) {
    return this.call('mcp_ui.api.ide.save_workflow', {
      ...data,
      states: data.states ? JSON.stringify(data.states) : undefined,
      transitions: data.transitions ? JSON.stringify(data.transitions) : undefined,
    });
  }

  async deleteWorkflow(name: string) {
    return this.call('mcp_ui.api.ide.delete_workflow', { name });
  }

  // Schema Management
  async getCustomFieldsForDoctype(doctype: string) {
    return this.call('mcp_ui.api.ide.get_custom_fields_for_doctype', { doctype });
  }

  async addCustomField(data: {
    dt: string; label: string; fieldtype: string;
    options?: string; insert_after?: string; reqd?: number;
    hidden?: number; default?: string; description?: string;
  }) {
    return this.call('mcp_ui.api.ide.add_custom_field', data);
  }

  async deleteCustomField(name: string) {
    return this.call('mcp_ui.api.ide.delete_custom_field', { name });
  }

  async getPropertySetters(doctype: string) {
    return this.call('mcp_ui.api.ide.get_property_setters', { doctype });
  }

  async setProperty(data: {
    doc_type: string; field_name: string; property: string;
    value: string; property_type?: string;
  }) {
    return this.call('mcp_ui.api.ide.set_property', data);
  }

  // Notifications
  async getNotificationRules() {
    return this.call('mcp_ui.api.ide.get_notifications');
  }

  async getNotificationRule(name: string) {
    return this.call('mcp_ui.api.ide.get_notification', { name });
  }

  // Hooks Discovery
  async getDocEvents() {
    return this.call('mcp_ui.api.ide.get_doc_events');
  }
}

// Export singleton instance
export const api = new FrappeAPI();

// Declare global types
declare global {
  interface Window {
    frappe?: {
      csrf_token?: string;
    };
    csrf_token?: string;
    boot_data?: {
      user: string;
      csrf_token: string;
      site_name: string;
      user_image?: string;
      full_name?: string;
    };
  }
}
