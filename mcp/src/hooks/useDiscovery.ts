/**
 * Hook to discover system information (apps, doctypes, etc.)
 */
import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { FrappeApp, DocType, CustomField, Workflow, SystemStats } from '@/types';

export function useInstalledApps() {
  return useQuery({
    queryKey: ['installed-apps'],
    queryFn: async () => {
      const response = await api.getInstalledApps();
      return response.apps as FrappeApp[];
    },
    staleTime: 10 * 60 * 1000, // 10 minutes
  });
}

export function useDocTypes(app?: string, module?: string) {
  return useQuery({
    queryKey: ['doctypes', app, module],
    queryFn: async () => {
      const response = await api.getDocTypes(app, module);
      return response.doctypes as DocType[];
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

export function useCustomFields(doctype?: string) {
  return useQuery({
    queryKey: ['custom-fields', doctype],
    queryFn: async () => {
      const response = await api.getCustomFields(doctype);
      return response.custom_fields as Record<string, CustomField[]>;
    },
    enabled: !!doctype,
    staleTime: 5 * 60 * 1000,
  });
}

export function useWorkflows() {
  return useQuery({
    queryKey: ['workflows'],
    queryFn: async () => {
      const response = await api.getWorkflows();
      return response.workflows as Workflow[];
    },
    staleTime: 5 * 60 * 1000,
  });
}

export function useSystemStats() {
  return useQuery({
    queryKey: ['system-stats'],
    queryFn: async () => {
      const response = await api.getSystemStats();
      return response.stats as SystemStats;
    },
    staleTime: 2 * 60 * 1000, // 2 minutes
  });
}

export function useDocTypeMeta(doctype?: string) {
  return useQuery({
    queryKey: ['doctype-meta', doctype],
    queryFn: async () => {
      if (!doctype) return null;
      const response = await api.getDocTypeMeta(doctype);
      return response.meta;
    },
    enabled: !!doctype,
    staleTime: 5 * 60 * 1000,
  });
}

