/**
 * Hook to execute MCP tools with credit tracking
 */
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { useCreditStore } from '@/stores/creditStore';
import { toast } from 'sonner';
import confetti from 'canvas-confetti';
import type { ToolExecutionResult } from '@/types';

export function useExecuteTool() {
  const queryClient = useQueryClient();
  const { deductCredits } = useCreditStore();

  return useMutation({
    mutationFn: async ({
      toolName,
      params,
    }: {
      toolName: string;
      params: Record<string, any>;
    }) => {
      const result = await api.executeTool(toolName, params);
      return result as ToolExecutionResult;
    },
    
    onSuccess: (data, variables) => {
      // Update credit balance
      queryClient.invalidateQueries({ queryKey: ['credits'] });
      queryClient.invalidateQueries({ queryKey: ['usage-history'] });
      
      // Show success message
      toast.success(`Tool "${variables.toolName}" executed successfully!`, {
        description: `${data.remaining_credits} credits remaining`,
      });
      
      // Trigger confetti animation
      confetti({
        particleCount: 100,
        spread: 70,
        origin: { y: 0.6 },
      });
    },
    
    onError: (error: Error, variables) => {
      toast.error(`Execution failed: ${variables.toolName}`, {
        description: error.message,
      });
    },
  });
}

