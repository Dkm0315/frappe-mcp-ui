/**
 * NaturalLanguageInput Component
 * Converts plain English to tool executions - NO TECHNICAL KNOWLEDGE REQUIRED
 */
import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Sparkles, ArrowRight, AlertTriangle } from 'lucide-react';
import type { NLPSuggestion } from '@/types';

interface NaturalLanguageInputProps {
  onToolSelect: (toolName: string, params: Record<string, any>, nextStep: string) => void;
  onAutoExecute?: (toolName: string, params: Record<string, any>) => void;
}

export function NaturalLanguageInput({ onToolSelect, onAutoExecute }: NaturalLanguageInputProps) {
  const [query, setQuery] = useState('');
  const [suggestions, setSuggestions] = useState<NLPSuggestion[]>([]);

  const parseMutation = useMutation({
    mutationFn: async (query: string) => {
      const response = await api.parseNaturalLanguage(query);
      return response;
    },
    onSuccess: (data) => {
      setSuggestions(data.suggestions || []);
      
      // Auto-execute if high confidence and complete params
      if (data.suggestions && data.suggestions.length > 0) {
        const topSuggestion = data.suggestions[0];
        if (
          topSuggestion.confidence === 'high' &&
          topSuggestion.tool &&
          topSuggestion.params &&
          topSuggestion.next_step === 'execute' &&
          onAutoExecute
        ) {
          // Execute directly for read-only operations
          if (['get_list', 'get_document', 'search_documents', 'get_dashboard_data'].includes(topSuggestion.tool)) {
            onAutoExecute(topSuggestion.tool, topSuggestion.params);
            setSuggestions([]); // Clear suggestions after auto-execute
          }
        }
      }
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      parseMutation.mutate(query);
    }
  };

  const handleSuggestionClick = (suggestion: NLPSuggestion) => {
    if (suggestion.tool && suggestion.params) {
      // Check if should auto-execute or show form
      if (
        suggestion.next_step === 'execute' &&
        !['create_document', 'update_document', 'delete_document'].includes(suggestion.tool) &&
        onAutoExecute
      ) {
        onAutoExecute(suggestion.tool, suggestion.params);
        setSuggestions([]);
      } else {
        onToolSelect(suggestion.tool, suggestion.params, suggestion.next_step || 'form');
      }
    }
  };

  return (
    <div className="space-y-6">
      {/* Main Search Input */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-primary" />
            What would you like to do?
          </CardTitle>
          <CardDescription>
            Just describe what you want in plain English
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="flex gap-2">
            <Input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder='e.g., "Create a new customer" or "Show all items"'
              className="text-base"
              disabled={parseMutation.isPending}
            />
            <Button type="submit" disabled={parseMutation.isPending || !query.trim()}>
              {parseMutation.isPending ? 'Thinking...' : 'Go'}
            </Button>
          </form>

          {/* Quick Examples */}
          <div className="mt-4 flex flex-wrap gap-2">
            <p className="text-xs text-muted-foreground w-full">Try these examples:</p>
            {[
              'Create a new customer',
              'Show all items',
              'Search for John in customers',
              'Get customer dashboard',
            ].map((example) => (
              <Badge
                key={example}
                variant="outline"
                className="cursor-pointer hover:bg-accent"
                onClick={() => setQuery(example)}
              >
                {example}
              </Badge>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Suggestions */}
      {suggestions.length > 0 && (
        <div className="space-y-3">
          <h3 className="text-sm font-medium">I can help you with:</h3>
          
          {suggestions.map((suggestion, idx) => (
            <Card
              key={idx}
              className={cn(
                'cursor-pointer transition-all hover:shadow-lg',
                suggestion.confidence === 'high' && 'border-primary/50',
                suggestion.warning && 'border-red-500/50'
              )}
              onClick={() => suggestion.tool && handleSuggestionClick(suggestion)}
            >
              <CardContent className="p-4">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <Badge
                        variant={
                          suggestion.confidence === 'high'
                            ? 'default'
                            : suggestion.confidence === 'medium'
                            ? 'secondary'
                            : 'outline'
                        }
                      >
                        {suggestion.confidence} confidence
                      </Badge>
                      {suggestion.next_step === 'execute' && !['create_document', 'update_document', 'delete_document'].includes(suggestion.tool || '') && (
                        <Badge variant="secondary" className="gap-1">
                          <Sparkles className="h-3 w-3" />
                          Auto-Execute
                        </Badge>
                      )}
                      {suggestion.next_step === 'form' && (
                        <Badge variant="outline" className="gap-1">
                          Form Required
                        </Badge>
                      )}
                      {suggestion.warning && (
                        <Badge variant="destructive" className="gap-1">
                          <AlertTriangle className="h-3 w-3" />
                          Warning
                        </Badge>
                      )}
                    </div>
                    
                    <p className="font-medium">{suggestion.description}</p>
                    
                    {suggestion.warning && (
                      <p className="mt-2 text-sm text-red-600">{suggestion.warning}</p>
                    )}
                    
                    {suggestion.message && (
                      <div className="mt-2">
                        <p className="text-sm text-muted-foreground">{suggestion.message}</p>
                        {suggestion.examples && (
                          <ul className="mt-2 space-y-1">
                            {suggestion.examples.map((example, i) => (
                              <li
                                key={i}
                                className="text-sm text-primary cursor-pointer hover:underline"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  setQuery(example);
                                }}
                              >
                                • {example}
                              </li>
                            ))}
                          </ul>
                        )}
                      </div>
                    )}
                  </div>
                  
                  {suggestion.tool && (
                    <ArrowRight className="h-5 w-5 text-muted-foreground" />
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

function cn(...classes: (string | boolean | undefined)[]): string {
  return classes.filter(Boolean).join(' ');
}

