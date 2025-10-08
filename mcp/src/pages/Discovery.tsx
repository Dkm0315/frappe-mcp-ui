/**
 * Discovery Page
 * Explore installed apps, doctypes, and system information
 */
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useInstalledApps, useSystemStats } from '@/hooks/useDiscovery';
import { Skeleton } from '@/components/ui/skeleton';
import { Badge } from '@/components/ui/badge';
import { Compass, Package, Database, Users, Cog } from 'lucide-react';

export function Discovery() {
  const { data: apps, isLoading: appsLoading } = useInstalledApps();
  const { data: stats, isLoading: statsLoading } = useSystemStats();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">System Discovery</h1>
        <p className="mt-2 text-muted-foreground">
          Explore your Frappe system configuration
        </p>
      </div>

      {/* System Stats */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {statsLoading ? (
          [...Array(4)].map((_, i) => <Skeleton key={i} className="h-24" />)
        ) : stats ? (
          <>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Apps</CardTitle>
                <Package className="size-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats.total_apps}</div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">DocTypes</CardTitle>
                <Database className="size-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats.total_doctypes}</div>
                <p className="text-xs text-muted-foreground">
                  +{stats.custom_doctypes} custom
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Users</CardTitle>
                <Users className="size-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats.total_users}</div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Workflows</CardTitle>
                <Cog className="size-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats.active_workflows}</div>
              </CardContent>
            </Card>
          </>
        ) : null}
      </div>

      {/* Installed Apps */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Compass className="size-5" />
            Installed Apps
          </CardTitle>
        </CardHeader>
        <CardContent>
          {appsLoading ? (
            <div className="grid gap-4 md:grid-cols-3">
              {[...Array(6)].map((_, i) => (
                <Skeleton key={i} className="h-24" />
              ))}
            </div>
          ) : apps && apps.length > 0 ? (
            <div className="grid gap-4 md:grid-cols-3">
              {apps.map((app) => (
                <Card key={app.name}>
                  <CardHeader>
                    <CardTitle className="text-base">{app.title[0] || app.name}</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="flex flex-wrap gap-1">
                      {app.modules.slice(0, 3).map((module) => (
                        <Badge key={module} variant="secondary" className="text-xs">
                          {module}
                        </Badge>
                      ))}
                      {app.modules.length > 3 && (
                        <Badge variant="outline" className="text-xs">
                          +{app.modules.length - 3}
                        </Badge>
                      )}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : (
            <p className="text-center text-muted-foreground">No apps found</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

