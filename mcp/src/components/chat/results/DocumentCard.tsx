/**
 * DocumentCard — Renders a single document as a rich form view
 * Uses FormView for proper field labels, status badges, currency formatting, etc.
 */
import { FormView } from './FormView';

export function DocumentCard({ result }: { result: any }) {
  const doc = result.data || {};
  const doctype = result.doctype || doc.doctype || '';
  const name = result.name || doc.name || '';

  return (
    <FormView
      data={doc}
      doctype={doctype}
      name={name}
      maxFields={16}
      showHeader={true}
    />
  );
}
