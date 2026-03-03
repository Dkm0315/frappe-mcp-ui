/**
 * Debug Console Page
 * System diagnostics, capabilities, hooks, and health monitoring
 */
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { useUIStore } from '@/stores/uiStore';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from '@/components/ui/table';
import {
  Bug, Shield, Activity, Webhook, RefreshCw, CheckCircle2,
  XCircle, AlertTriangle, Server, Database, Zap, Copy,
} from 'lucide-react';
import { toast } from 'sonner';

// ── Capabilities Tab ───────────────────────────────────────────────
function CapabilitiesTab() {
  const { data, isLoading, refetch } = useQuery({
    queryKey: ['capabilities'],
    queryFn: async () => {
      const res = await api.getCapabilities();
      return res;
    },
  });

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold">System Capabilities</h3>
        <Button size="sm" variant="outline" onClick={() => refetch()}>
          <RefreshCw className="mr-1 size-3" /> Refresh
        </Button>
      </div>

      {isLoading ? (
        <Skeleton className="h-48" />
      ) : data ? (
        <div className="space-y-4">
          {/* Key Capabilities */}
          <div className="grid gap-4 sm:grid-cols-2">
            <Card>
              <CardContent className="pt-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Server className="size-4" />
                    <span className="text-sm font-medium">Server Scripts</span>
                  </div>
                  {data.server_scripts_enabled ? (
                    <Badge variant="default" className="flex items-center gap-1">
                      <CheckCircle2 className="size-3" /> Enabled
                    </Badge>
                  ) : (
                    <Badge variant="secondary" className="flex items-center gap-1">
                      <XCircle className="size-3" /> Disabled
                    </Badge>
                  )}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Shield className="size-4" />
                    <span className="text-sm font-medium">Script Manager Role</span>
                  </div>
                  {data.has_script_manager ? (
                    <Badge variant="default" className="flex items-center gap-1">
                      <CheckCircle2 className="size-3" /> Yes
                    </Badge>
                  ) : (
                    <Badge variant="secondary" className="flex items-center gap-1">
                      <XCircle className="size-3" /> No
                    </Badge>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* User Roles */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm">
                User Roles ({data.user_roles?.length || 0})
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-1">
                {data.user_roles?.map((role: string) => (
                  <Badge key={role} variant="outline" className="text-xs">
                    {role}
                  </Badge>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Capability Matrix */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm">Feature Availability</CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Feature</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Requirement</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {[
                    { feature: 'Client Scripts', available: true, req: 'None' },
                    { feature: 'Server Scripts', available: data.server_scripts_enabled, req: 'server_script_enabled: 1' },
                    { feature: 'Workflows', available: true, req: 'None' },
                    { feature: 'Custom Fields', available: true, req: 'None' },
                    { feature: 'Property Setters', available: true, req: 'None' },
                    { feature: 'Notifications', available: true, req: 'None' },
                    { feature: 'API Endpoints', available: data.server_scripts_enabled, req: 'server_script_enabled: 1' },
                    { feature: 'Scheduled Jobs', available: data.server_scripts_enabled, req: 'server_script_enabled: 1' },
                  ].map((item) => (
                    <TableRow key={item.feature}>
                      <TableCell className="font-medium">{item.feature}</TableCell>
                      <TableCell>
                        {item.available ? (
                          <Badge variant="default" className="text-[10px]">
                            <CheckCircle2 className="mr-1 size-3" /> Available
                          </Badge>
                        ) : (
                          <Badge variant="secondary" className="text-[10px]">
                            <XCircle className="mr-1 size-3" /> Unavailable
                          </Badge>
                        )}
                      </TableCell>
                      <TableCell className="text-xs text-muted-foreground">{item.req}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </div>
      ) : null}
    </div>
  );
}

// ── Doc Events Tab ─────────────────────────────────────────────────
function DocEventsTab() {
  const { data, isLoading, refetch } = useQuery({
    queryKey: ['doc-events'],
    queryFn: async () => {
      const res = await api.getDocEvents();
      return res.doc_events as Record<string, any>;
    },
  });

  const copyAll = () => {
    navigator.clipboard.writeText(JSON.stringify(data, null, 2));
    toast.success('Copied to clipboard');
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold">Registered Doc Events</h3>
        <div className="flex gap-2">
          <Button size="sm" variant="outline" onClick={copyAll}>
            <Copy className="mr-1 size-3" /> Copy JSON
          </Button>
          <Button size="sm" variant="outline" onClick={() => refetch()}>
            <RefreshCw className="mr-1 size-3" /> Refresh
          </Button>
        </div>
      </div>

      {isLoading ? (
        <Skeleton className="h-48" />
      ) : data ? (
        <div className="space-y-3">
          {Object.keys(data).length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              No doc_events hooks registered
            </div>
          ) : (
            Object.entries(data).map(([doctype, events]) => (
              <Card key={doctype}>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm flex items-center gap-2">
                    <Database className="size-3" />
                    {doctype}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <ScrollArea className="max-h-48">
                    <pre className="rounded bg-muted p-2 text-xs font-mono">
                      {JSON.stringify(events, null, 2)}
                    </pre>
                  </ScrollArea>
                </CardContent>
              </Card>
            ))
          )}
        </div>
      ) : null}
    </div>
  );
}

// ── System Health Tab ──────────────────────────────────────────────
function HealthTab() {
  const { data, isLoading, refetch } = useQuery({
    queryKey: ['system-health'],
    queryFn: async () => {
      const res = await api.getSystemHealth();
      return res;
    },
  });

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold">System Health</h3>
        <Button size="sm" variant="outline" onClick={() => refetch()}>
          <RefreshCw className="mr-1 size-3" /> Refresh
        </Button>
      </div>

      {isLoading ? (
        <Skeleton className="h-48" />
      ) : data ? (
        <Card>
          <CardContent className="pt-4">
            <ScrollArea className="max-h-[400px]">
              <pre className="rounded bg-muted p-3 text-xs font-mono">
                {JSON.stringify(data, null, 2)}
              </pre>
            </ScrollArea>
          </CardContent>
        </Card>
      ) : (
        <Alert>
          <AlertTriangle className="size-4" />
          <AlertDescription>Could not fetch system health data.</AlertDescription>
        </Alert>
      )}
    </div>
  );
}

// ── Notifications Tab ──────────────────────────────────────────────
function NotificationsTab() {
  const [selected, setSelected] = useState<string | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ['ide-notifications'],
    queryFn: async () => {
      const res = await api.getNotificationRules();
      return res.notifications as any[];
    },
  });

  const { data: detail } = useQuery({
    queryKey: ['ide-notification', selected],
    queryFn: async () => {
      if (!selected) return null;
      const res = await api.getNotificationRule(selected);
      return res.notification;
    },
    enabled: !!selected,
  });

  return (
    <div className="space-y-4">
      <h3 className="text-sm font-semibold">
        Notification Rules ({data?.length || 0})
      </h3>

      {isLoading ? (
        <Skeleton className="h-48" />
      ) : !data || data.length === 0 ? (
        <div className="text-center py-8 text-muted-foreground">
          No notification rules configured
        </div>
      ) : (
        <div className="grid gap-4 lg:grid-cols-2">
          {/* List */}
          <Card>
            <CardContent className="p-0">
              <ScrollArea className="h-[400px]">
                <div className="divide-y">
                  {data.map((n: any) => (
                    <button
                      key={n.name}
                      className={`w-full px-4 py-3 text-left hover:bg-accent transition-colors ${
                        selected === n.name ? 'bg-accent' : ''
                      }`}
                      onClick={() => setSelected(n.name)}
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium truncate">{n.name}</span>
                        <Badge variant={n.enabled ? 'default' : 'secondary'} className="text-[10px]">
                          {n.enabled ? 'ON' : 'OFF'}
                        </Badge>
                      </div>
                      <div className="flex gap-2 mt-1 text-xs text-muted-foreground">
                        <span>{n.document_type}</span>
                        <span>· {n.event}</span>
                        <span>· {n.channel}</span>
                      </div>
                    </button>
                  ))}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>

          {/* Detail */}
          <Card>
            <CardContent className="pt-4">
              {detail ? (
                <ScrollArea className="h-[400px]">
                  <pre className="rounded bg-muted p-3 text-xs font-mono">
                    {JSON.stringify(detail, null, 2)}
                  </pre>
                </ScrollArea>
              ) : (
                <div className="flex h-40 items-center justify-center text-muted-foreground">
                  Select a notification to view details
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}

// ── Main Page ──────────────────────────────────────────────────────
export function DebugConsole() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold flex items-center gap-3">
          <Bug className="size-8 text-primary" />
          Debug Console
        </h1>
        <p className="mt-2 text-muted-foreground">
          System diagnostics, capabilities, hooks, and notifications
        </p>
      </div>

      <Tabs defaultValue="capabilities">
        <TabsList className="flex-wrap">
          <TabsTrigger value="capabilities" className="flex items-center gap-2">
            <Shield className="size-4" /> Capabilities
          </TabsTrigger>
          <TabsTrigger value="doc-events" className="flex items-center gap-2">
            <Webhook className="size-4" /> Doc Events
          </TabsTrigger>
          <TabsTrigger value="health" className="flex items-center gap-2">
            <Activity className="size-4" /> Health
          </TabsTrigger>
          <TabsTrigger value="notifications" className="flex items-center gap-2">
            <Zap className="size-4" /> Notifications
          </TabsTrigger>
        </TabsList>

        <TabsContent value="capabilities" className="mt-4">
          <CapabilitiesTab />
        </TabsContent>

        <TabsContent value="doc-events" className="mt-4">
          <DocEventsTab />
        </TabsContent>

        <TabsContent value="health" className="mt-4">
          <HealthTab />
        </TabsContent>

        <TabsContent value="notifications" className="mt-4">
          <NotificationsTab />
        </TabsContent>
      </Tabs>
    </div>
  );
}
