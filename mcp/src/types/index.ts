/**
 * TypeScript type definitions for MCP UI
 */

export interface MCPTool {
  name: string;
  title: string;
  description: string;
  category: 'CRUD' | 'Query' | 'Reports' | 'Bulk' | 'Export' | 'Analytics';
  base_cost: number;
  destructive: boolean;
  read_only: boolean;
}

export interface ToolExecutionResult {
  success: boolean;
  result: any;
  tool: string;
  remaining_credits: number;
}

export interface CreditBalance {
  balance: number;
  total_purchased: number;
  total_consumed: number;
}

export interface UsageLog {
  name: string;
  tool_name: string;
  credits_consumed: number;
  status: 'Success' | 'Failed' | 'Partial';
  creation: string;
  input_params?: string;
  output?: string;
  error_message?: string;
}

export interface CreditPackage {
  name: string;
  package_name: string;
  credits: number;
  price: number;
  description?: string;
}

export interface FrappeApp {
  name: string;
  title: string[];
  modules: string[];
}

export interface DocType {
  name: string;
  module: string;
  app_name: string;
  is_submittable: boolean;
  is_tree: boolean;
  issingle: boolean;
  editable_grid: boolean;
  track_changes: boolean;
}

export interface CustomField {
  name: string;
  dt: string;
  fieldname: string;
  fieldtype: string;
  label: string;
  options?: string;
  insert_after?: string;
}

export interface Workflow {
  name: string;
  document_type: string;
  workflow_name: string;
  workflow_state_field: string;
  states?: WorkflowState[];
}

export interface WorkflowState {
  state: string;
  doc_status: string;
  update_field?: string;
  update_value?: string;
}

export interface SystemStats {
  total_apps: number;
  total_doctypes: number;
  custom_doctypes: number;
  total_users: number;
  total_custom_fields: number;
  active_workflows: number;
}

export interface JSONSchema {
  type: string;
  properties?: Record<string, any>;
  required?: string[];
  items?: any;
  default?: any;
  description?: string;
}

export type UIMode = 'simple' | 'advanced' | 'workflows';

export interface FormField {
  fieldname: string;
  label: string;
  fieldtype: string;
  required: boolean;
  description?: string;
  default?: any;
  input_type: 'text' | 'number' | 'select' | 'checkbox' | 'date' | 'datetime' | 'time' | 'textarea' | 'richtext' | 'autocomplete';
  options?: string[];
  link_doctype?: string;
  number_type?: 'integer' | 'decimal';
}

export interface DocTypeFormSchema {
  success: boolean;
  doctype: string;
  title_field?: string;
  fields: FormField[];
}

export interface LinkFieldOption {
  value: string;
  label: string;
  description?: string;
}

export interface QuickTemplate {
  doctype: string;
  icon: string;
  title: string;
  description: string;
  fields: string[];
}

export interface NLPSuggestion {
  confidence: 'high' | 'medium' | 'low';
  tool?: string;
  params?: Record<string, any>;
  description?: string;
  next_step?: 'form' | 'execute' | 'confirm';
  warning?: string;
  message?: string;
  examples?: string[];
}

export interface NLPResponse {
  success: boolean;
  query: string;
  suggestions: NLPSuggestion[];
}
