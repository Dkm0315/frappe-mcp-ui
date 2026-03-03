/**
 * GenericResult — Auto-form fallback for tools without a dedicated renderer
 * Renders structured data as a form instead of raw JSON.
 */
import { useState } from 'react';
import { ChevronDown, Wrench } from 'lucide-react';
import { cn } from '@/lib/utils';
import { FormView } from './FormView';

export function GenericResult({ result, toolName }: { result: any; toolName: string }) {
  const label = toolName.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());

  // If result has a data object or is itself a flat object, render as form
  const formData = result.data || result;

  // Check if it's a flat-ish object we can render as a form
  if (typeof formData === 'object' && formData !== null && !Array.isArray(formData)) {
    return (
      <div className="rounded-xl border border-border/50 overflow-hidden">
        <div className="bg-muted/30 px-4 py-2.5 border-b border-border/30 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Wrench className="size-3.5 text-muted-foreground" />
            <span className="text-xs font-semibold text-foreground">{label}</span>
          </div>
          {result.success && (
            <span className="text-[10px] text-emerald-500 font-semibold">Success</span>
          )}
        </div>
        <FormView
          data={formData}
          doctype={result.doctype}
          name={result.name}
          maxFields={20}
          showHeader={false}
        />
      </div>
    );
  }

  // For non-object results (strings, numbers, arrays of primitives), show simple display
  return (
    <div className="rounded-xl border border-border/50 overflow-hidden">
      <div className="bg-muted/30 px-4 py-2.5 border-b border-border/30 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Wrench className="size-3.5 text-muted-foreground" />
          <span className="text-xs font-semibold text-foreground">{label}</span>
        </div>
        {result.success && (
          <span className="text-[10px] text-emerald-500 font-semibold">Success</span>
        )}
      </div>
      <div className="px-4 py-3 text-sm text-foreground">
        {typeof formData === 'string' ? formData : JSON.stringify(formData, null, 2)}
      </div>
    </div>
  );
}
