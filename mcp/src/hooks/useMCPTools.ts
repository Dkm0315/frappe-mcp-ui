/**
 * Hook to fetch available MCP tools
 */
import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { MCPTool } from '@/types';

export function useMCPTools() {
  return useQuery({
    queryKey: ['mcp-tools'],
    queryFn: async () => {
      const response = await api.getTools();
      return response.tools as MCPTool[];
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

