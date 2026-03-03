/**
 * Result Renderer — Dispatches tool results to specialized form-style components
 * Every tool result is rendered as a proper form/card, never as raw JSON.
 */
import { DataTable } from './DataTable';
import { DocumentCard } from './DocumentCard';
import { SuccessCard } from './SuccessCard';
import { DeleteCard } from './DeleteCard';
import { BulkResult } from './BulkResult';
import { StatsCard } from './StatsCard';
import { SearchResults } from './SearchResults';
import { WebResults } from './WebResults';
import { WorkflowInfo } from './WorkflowInfo';
import { ProcessChain } from './ProcessChain';
import { ExcelPreview } from './ExcelPreview';
import { GenericResult } from './GenericResult';

interface ResultRendererProps {
  toolName: string;
  result: any;
}

export function ResultRenderer({ toolName, result }: ResultRendererProps) {
  if (!result || result.error) {
    return (
      <div className="rounded-xl border border-red-500/20 bg-red-500/5 px-4 py-3 text-sm text-red-600">
        {result?.error || 'Tool execution failed'}
      </div>
    );
  }

  switch (toolName) {
    // Tables & reports
    case 'get_list':
    case 'run_report':
    case 'analyze_data':
    case 'export_to_excel':
      return <DataTable result={result} toolName={toolName} />;

    // Single document view
    case 'get_document':
      return <DocumentCard result={result} />;

    // Success operations (with expandable form view)
    case 'create_document':
    case 'update_document':
    case 'submit_document':
    case 'cancel_document':
    case 'amend_document':
      return <SuccessCard result={result} toolName={toolName} />;

    // Delete
    case 'delete_document':
      return <DeleteCard result={result} />;

    // Process chains
    case 'make_mapped_document':
    case 'get_linked_documents':
      return <ProcessChain result={result} toolName={toolName} />;

    // Bulk operations
    case 'bulk_create':
    case 'bulk_update':
    case 'bulk_delete':
    case 'import_from_excel':
      return <BulkResult result={result} toolName={toolName} />;

    // Excel preview
    case 'parse_excel':
      return <ExcelPreview result={result} />;

    // Search results
    case 'search_documents':
      return <SearchResults result={result} />;

    // Statistics
    case 'get_count':
    case 'get_dashboard_data':
      return <StatsCard result={result} toolName={toolName} />;

    // Workflow
    case 'get_workflow_info':
    case 'get_pending_approvals':
      return <WorkflowInfo result={result} toolName={toolName} />;

    // Web search
    case 'web_search':
      return <WebResults result={result} />;

    // DocType metadata & automation — use generic form view
    case 'get_doctype_meta':
    case 'execute_automation_chain':
    default:
      return <GenericResult result={result} toolName={toolName} />;
  }
}
