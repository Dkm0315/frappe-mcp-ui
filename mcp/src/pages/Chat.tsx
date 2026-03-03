/**
 * Chat Page — AI Business Automation Engine
 * Uses Vercel AI SDK useChat() with streaming UI Message Stream Protocol.
 * Tools execute server-side; results render as rich cards.
 * Supports file uploads (PDF, Excel, images) and tool selector.
 */
import { useState, useRef, useEffect, useMemo, useCallback } from 'react';
import { useChat } from '@ai-sdk/react';
import { DefaultChatTransport } from 'ai';
import { cn } from '@/lib/utils';
import { ResultRenderer } from '@/components/chat/results/ResultRenderer';
import {
  Bot, User, Sparkles, ArrowUp, Square, Loader2,
  Paperclip, Globe, FileSpreadsheet, Image, FileText,
  X, File, Plus,
} from 'lucide-react';

// ── File attachment type ────────────────────────────────────────────
interface Attachment {
  name: string;
  file_url: string;
  type: 'image' | 'pdf' | 'excel' | 'other';
  size: number;
}

function getFileType(name: string): Attachment['type'] {
  const ext = name.split('.').pop()?.toLowerCase() || '';
  if (['png', 'jpg', 'jpeg', 'gif', 'webp', 'svg'].includes(ext)) return 'image';
  if (ext === 'pdf') return 'pdf';
  if (['xlsx', 'xls', 'csv'].includes(ext)) return 'excel';
  return 'other';
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

// ── Tool selector items ─────────────────────────────────────────────
const toolActions = [
  { id: 'web_search', label: 'Web Search', icon: Globe, prompt: 'Search the web for: ' },
  { id: 'parse_excel', label: 'Import Excel', icon: FileSpreadsheet, prompt: 'Parse and import the uploaded Excel file' },
  { id: 'run_report', label: 'Run Report', icon: FileText, prompt: 'Run the report: ' },
];

export function Chat() {
  const [input, setInput] = useState('');
  const [attachments, setAttachments] = useState<Attachment[]>([]);
  const [uploading, setUploading] = useState(false);
  const [showToolMenu, setShowToolMenu] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const toolMenuRef = useRef<HTMLDivElement>(null);

  const transport = useMemo(() => new DefaultChatTransport({
    api: '/api/method/mcp_ui.api.ai_chat.stream',
    headers: {
      'X-Frappe-CSRF-Token': (window as any).csrf_token || '',
    },
  }), []);

  const { messages, sendMessage, status, stop, error } = useChat({
    transport,
  });

  const isStreaming = status === 'streaming' || status === 'submitted';

  // Auto-scroll on new messages
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, status]);

  // Close tool menu on click outside
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (toolMenuRef.current && !toolMenuRef.current.contains(e.target as Node)) {
        setShowToolMenu(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  // File upload handler
  const uploadFile = useCallback(async (file: globalThis.File) => {
    setUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('is_private', '0');
      formData.append('folder', 'Home/Attachments');

      const res = await fetch('/api/method/upload_file', {
        method: 'POST',
        headers: {
          'X-Frappe-CSRF-Token': (window as any).csrf_token || '',
        },
        body: formData,
      });

      const data = await res.json();
      if (data.message?.file_url) {
        const attachment: Attachment = {
          name: file.name,
          file_url: data.message.file_url,
          type: getFileType(file.name),
          size: file.size,
        };
        setAttachments(prev => [...prev, attachment]);
      }
    } catch (err) {
      console.error('Upload failed:', err);
    } finally {
      setUploading(false);
    }
  }, []);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files) {
      Array.from(files).forEach(uploadFile);
    }
    e.target.value = '';
  };

  const removeAttachment = (idx: number) => {
    setAttachments(prev => prev.filter((_, i) => i !== idx));
  };

  // Drag and drop
  const [isDragging, setIsDragging] = useState(false);
  const handleDragOver = (e: React.DragEvent) => { e.preventDefault(); setIsDragging(true); };
  const handleDragLeave = () => setIsDragging(false);
  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const files = e.dataTransfer.files;
    if (files) Array.from(files).forEach(uploadFile);
  };

  const handleSend = () => {
    const text = input.trim();
    if ((!text && attachments.length === 0) || isStreaming) return;

    // Build message with attachment context
    let content = text;
    if (attachments.length > 0) {
      const fileList = attachments.map(a =>
        `[Attached: ${a.name} (${a.type}, ${formatFileSize(a.size)}) — ${window.location.origin}${a.file_url}]`
      ).join('\n');
      content = fileList + (text ? '\n\n' + text : '\n\nPlease analyze the attached file(s).');
    }

    setInput('');
    setAttachments([]);
    sendMessage({ role: 'user', content });
    inputRef.current?.focus();
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleToolAction = (prompt: string) => {
    setShowToolMenu(false);
    setInput(prompt);
    inputRef.current?.focus();
  };

  const quickActions = [
    'Show all Sales Orders',
    'How many active users?',
    'What approvals are pending for me?',
    'Run the Accounts Receivable report',
  ];

  return (
    <div
      className="flex h-[calc(100vh-8rem)] flex-col max-w-2xl mx-auto"
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      {/* Drag overlay */}
      {isDragging && (
        <div className="absolute inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm border-2 border-dashed border-primary/40 rounded-xl m-4">
          <div className="text-center">
            <Paperclip className="size-8 text-primary mx-auto mb-2" />
            <p className="text-sm font-medium text-primary">Drop files here</p>
            <p className="text-xs text-muted-foreground">PDF, Excel, Images</p>
          </div>
        </div>
      )}

      {/* Messages */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto px-1 py-6 space-y-6">
        {/* Welcome message if no messages */}
        {messages.length === 0 && (
          <div className="flex gap-3">
            <div className="flex size-8 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-primary/20 to-primary/5 border border-primary/10">
              <Bot className="size-4 text-primary" />
            </div>
            <div className="max-w-[80%]">
              <div className="inline-block rounded-2xl rounded-bl-md bg-muted/50 border border-border/50 px-4 py-3">
                <div className="text-sm leading-relaxed">
                  <p>Hi! I'm your Frappe business automation engine. I can do much more than answer questions — I execute entire business processes.</p>
                  <p className="mt-2 text-muted-foreground text-xs">Try things like:</p>
                  <ul className="mt-1 text-xs text-muted-foreground space-y-0.5">
                    <li>- "Create a Delivery Note from SO-00145"</li>
                    <li>- "Show me all overdue Sales Invoices"</li>
                    <li>- "Run the Accounts Receivable report"</li>
                    <li>- Upload an Excel file and say "Import these as Sales Invoices"</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        )}

        {messages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} />
        ))}

        {/* Streaming indicator */}
        {isStreaming && messages.length > 0 && (
          (() => {
            const lastMsg = messages[messages.length - 1];
            const hasContent = lastMsg?.role === 'assistant' && lastMsg.parts?.some(
              (p: any) => (p.type === 'text' && p.text?.trim()) || isToolPart(p)
            );
            if (hasContent) return null;
            return <ThinkingIndicator />;
          })()
        )}

        {/* Error display */}
        {error && (
          <div className="flex gap-3">
            <div className="flex size-8 shrink-0 items-center justify-center rounded-full bg-red-500/10 border border-red-500/20">
              <Bot className="size-4 text-red-500" />
            </div>
            <div className="inline-block rounded-2xl rounded-bl-md bg-red-500/5 border border-red-500/20 px-4 py-3">
              <p className="text-sm text-red-600">{error.message || 'Something went wrong. Please try again.'}</p>
            </div>
          </div>
        )}
      </div>

      {/* Input area */}
      <div className="border-t border-border/50 pt-3 pb-2 space-y-2">
        {/* Attachment previews */}
        {attachments.length > 0 && (
          <div className="flex flex-wrap gap-2 px-1">
            {attachments.map((att, i) => (
              <div key={i} className="flex items-center gap-2 rounded-xl border border-border/50 bg-muted/30 px-3 py-1.5 text-xs">
                {att.type === 'image' ? <Image className="size-3.5 text-blue-500" /> :
                 att.type === 'pdf' ? <FileText className="size-3.5 text-red-500" /> :
                 att.type === 'excel' ? <FileSpreadsheet className="size-3.5 text-green-500" /> :
                 <File className="size-3.5 text-muted-foreground" />}
                <span className="max-w-[120px] truncate">{att.name}</span>
                <span className="text-muted-foreground">{formatFileSize(att.size)}</span>
                <button onClick={() => removeAttachment(i)} className="ml-1 hover:text-destructive">
                  <X className="size-3" />
                </button>
              </div>
            ))}
          </div>
        )}

        {/* Input row */}
        <div className="flex gap-2 items-end">
          {/* Tool menu + attach button */}
          <div className="flex gap-1 shrink-0">
            {/* Attach file */}
            <button
              onClick={() => fileInputRef.current?.click()}
              disabled={isStreaming || uploading}
              className="flex size-10 items-center justify-center rounded-xl border border-border/50 bg-muted/30 text-muted-foreground hover:text-foreground hover:bg-muted/60 transition-all disabled:opacity-40"
              title="Attach file (PDF, Excel, Image)"
            >
              {uploading ? <Loader2 className="size-4 animate-spin" /> : <Paperclip className="size-4" />}
            </button>
            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept=".pdf,.xlsx,.xls,.csv,.png,.jpg,.jpeg,.gif,.webp"
              onChange={handleFileSelect}
              className="hidden"
            />

            {/* Tool selector */}
            <div className="relative" ref={toolMenuRef}>
              <button
                onClick={() => setShowToolMenu(!showToolMenu)}
                disabled={isStreaming}
                className={cn(
                  'flex size-10 items-center justify-center rounded-xl border border-border/50 bg-muted/30 text-muted-foreground hover:text-foreground hover:bg-muted/60 transition-all disabled:opacity-40',
                  showToolMenu && 'bg-primary/10 border-primary/30 text-primary'
                )}
                title="Tools"
              >
                <Plus className={cn('size-4 transition-transform', showToolMenu && 'rotate-45')} />
              </button>

              {/* Tool dropdown */}
              {showToolMenu && (
                <div className="absolute bottom-full left-0 mb-2 w-48 rounded-xl border border-border/50 bg-background shadow-lg overflow-hidden z-50">
                  {toolActions.map(tool => (
                    <button
                      key={tool.id}
                      onClick={() => handleToolAction(tool.prompt)}
                      className="flex items-center gap-2.5 w-full px-3 py-2.5 text-xs text-left hover:bg-muted/50 transition-colors"
                    >
                      <tool.icon className="size-3.5 text-primary/70" />
                      <span>{tool.label}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Text input */}
          <div className="relative flex-1">
            <Sparkles className="absolute left-3.5 top-1/2 -translate-y-1/2 size-4 text-primary/30" />
            <input
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={attachments.length > 0 ? 'Describe what to do with the file...' : 'Ask anything or give a command...'}
              disabled={isStreaming}
              className="w-full rounded-2xl border border-border/50 bg-muted/30 px-4 py-3 pl-10 text-sm placeholder:text-muted-foreground/40 focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary/30 focus:bg-background transition-all disabled:opacity-50"
            />
          </div>

          {/* Send / Stop */}
          {isStreaming ? (
            <button
              onClick={() => stop()}
              className="flex size-11 items-center justify-center rounded-2xl bg-destructive text-destructive-foreground shrink-0 shadow-sm hover:bg-destructive/90 transition-colors"
            >
              <Square className="size-4" />
            </button>
          ) : (
            <button
              onClick={handleSend}
              disabled={!input.trim() && attachments.length === 0}
              className="flex size-11 items-center justify-center rounded-2xl bg-primary text-primary-foreground shrink-0 shadow-sm shadow-primary/10 disabled:opacity-40 hover:bg-primary/90 transition-colors"
            >
              <ArrowUp className="size-4" />
            </button>
          )}
        </div>

        {/* Quick actions */}
        <div className="flex flex-wrap gap-1.5 px-0.5">
          {quickActions.map(action => (
            <button
              key={action}
              onClick={() => { setInput(action); inputRef.current?.focus(); }}
              disabled={isStreaming}
              className="rounded-full border border-border/50 bg-muted/30 px-3 py-1.5 text-[11px] text-muted-foreground hover:text-foreground hover:bg-muted/60 hover:border-primary/20 transition-all disabled:opacity-40"
            >
              {action}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

// ── Thinking Indicator ──────────────────────────────────────────────
function ThinkingIndicator() {
  return (
    <div className="flex gap-3">
      <div className="flex size-8 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-primary/20 to-primary/5 border border-primary/10">
        <Bot className="size-4 text-primary" />
      </div>
      <div className="flex items-center gap-2 rounded-2xl rounded-bl-md bg-muted/50 border border-border/50 px-5 py-3">
        <div className="flex gap-1">
          <span className="size-2 rounded-full bg-primary/40 animate-bounce [animation-delay:0ms]" />
          <span className="size-2 rounded-full bg-primary/40 animate-bounce [animation-delay:150ms]" />
          <span className="size-2 rounded-full bg-primary/40 animate-bounce [animation-delay:300ms]" />
        </div>
        <span className="text-xs text-muted-foreground ml-1">Thinking...</span>
      </div>
    </div>
  );
}

// ── AI SDK v6 Part Helpers ───────────────────────────────────────────
function isToolPart(part: any): boolean {
  return part.type === 'dynamic-tool' || (typeof part.type === 'string' && part.type.startsWith('tool-'));
}

function getToolName(part: any): string {
  if (part.type === 'dynamic-tool') return part.toolName || 'unknown';
  return part.type.slice(5); // 'tool-get_count' → 'get_count'
}

// ── Message Bubble ──────────────────────────────────────────────────
function MessageBubble({ message }: { message: any }) {
  const isUser = message.role === 'user';

  return (
    <div className={cn('flex gap-3', isUser && 'flex-row-reverse')}>
      <div className={cn(
        'flex size-8 shrink-0 items-center justify-center rounded-full',
        isUser
          ? 'bg-gradient-to-br from-primary to-primary/80 text-primary-foreground shadow-sm shadow-primary/20'
          : 'bg-gradient-to-br from-primary/20 to-primary/5 border border-primary/10'
      )}>
        {isUser ? <User className="size-4" /> : <Bot className="size-4 text-primary" />}
      </div>
      <div className={cn('max-w-[85%] space-y-2', isUser && 'text-right')}>
        {/* Render message parts */}
        {message.parts?.map((part: any, i: number) => {
          if (part.type === 'text' && part.text) {
            return (
              <div key={i} className={cn(
                'inline-block rounded-2xl px-4 py-3',
                isUser
                  ? 'bg-primary text-primary-foreground rounded-br-md'
                  : 'bg-muted/50 border border-border/50 rounded-bl-md'
              )}>
                <div className="text-sm leading-relaxed whitespace-pre-wrap">
                  {renderMarkdown(part.text)}
                </div>
              </div>
            );
          }

          // AI SDK v6: tool parts have type 'tool-{name}' or 'dynamic-tool'
          if (isToolPart(part)) {
            const toolName = getToolName(part);
            return (
              <div key={i} className="text-left">
                {(part.state === 'input-streaming' || part.state === 'input-available') && (
                  <div className="flex items-center gap-2 text-xs text-muted-foreground py-1">
                    <Loader2 className="size-3 animate-spin" />
                    <span>Running {formatToolName(toolName)}...</span>
                  </div>
                )}
                {part.state === 'output-available' && part.output != null && (
                  <ResultRenderer toolName={toolName} result={part.output} />
                )}
                {part.state === 'output-error' && (
                  <div className="rounded-xl border border-red-500/20 bg-red-500/5 px-4 py-3 text-sm text-red-600">
                    {part.errorText || 'Tool execution failed'}
                  </div>
                )}
              </div>
            );
          }

          return null;
        })}

        {/* Fallback: render content directly if no parts */}
        {!message.parts?.length && message.content && (
          <div className={cn(
            'inline-block rounded-2xl px-4 py-3',
            isUser
              ? 'bg-primary text-primary-foreground rounded-br-md'
              : 'bg-muted/50 border border-border/50 rounded-bl-md'
          )}>
            <div className="text-sm leading-relaxed whitespace-pre-wrap">
              {renderMarkdown(message.content)}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// ── Helpers ──────────────────────────────────────────────────────────
function formatToolName(name: string): string {
  return name.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
}

function renderMarkdown(text: string) {
  // Split by code blocks
  const parts = text.split(/(`{3}[\s\S]*?`{3}|`[^`]+`)/g);
  return parts.map((part, i) => {
    if (part.startsWith('```')) {
      const code = part.replace(/^```\w*\n?/, '').replace(/\n?```$/, '');
      return <pre key={i} className="my-2 rounded-lg bg-background/50 border p-3 text-xs overflow-x-auto font-mono">{code}</pre>;
    }
    if (part.startsWith('`') && part.endsWith('`')) {
      return <code key={i} className="rounded bg-background/50 px-1.5 py-0.5 text-xs font-mono">{part.slice(1, -1)}</code>;
    }
    // Inline: bold, italic, lists
    const segments = part.split(/(\*\*[^*]+\*\*|_[^_]+_)/g);
    return (
      <span key={i}>
        {segments.map((seg, j) => {
          if (seg.startsWith('**') && seg.endsWith('**')) return <strong key={j}>{seg.slice(2, -2)}</strong>;
          if (seg.startsWith('_') && seg.endsWith('_') && seg.length > 2) return <em key={j}>{seg.slice(1, -1)}</em>;
          return seg;
        })}
      </span>
    );
  });
}
