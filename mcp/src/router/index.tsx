/**
 * React Router Configuration
 * Routes for all three modes: Admin, Developer, Assistant
 */
import { createBrowserRouter, RouterProvider } from 'react-router-dom';
import { AppShell } from '@/components/layout/AppShell';
import { Dashboard } from '@/pages/Dashboard';
import { Tools } from '@/pages/Tools';
import { Workflows } from '@/pages/Workflows';
import { History } from '@/pages/History';
import { Credits } from '@/pages/Credits';
import { Settings } from '@/pages/Settings';
import { Discovery } from '@/pages/Discovery';
import { ScriptStudio } from '@/pages/ScriptStudio';
import { WorkflowBuilder } from '@/pages/WorkflowBuilder';
import { SchemaManager } from '@/pages/SchemaManager';
import { FeatureFlags } from '@/pages/FeatureFlags';
import { Chat } from '@/pages/Chat';
import { ApiExplorer } from '@/pages/ApiExplorer';
import { DebugConsole } from '@/pages/DebugConsole';

const router = createBrowserRouter(
  [
    {
      path: '/',
      element: <AppShell />,
      children: [
        // Shared routes
        { index: true, element: <Dashboard /> },
        { path: 'tools', element: <Tools /> },
        { path: 'history', element: <History /> },
        { path: 'credits', element: <Credits /> },
        { path: 'discovery', element: <Discovery /> },
        { path: 'settings', element: <Settings /> },

        // Admin routes
        { path: 'workflows', element: <Workflows /> },
        { path: 'feature-flags', element: <FeatureFlags /> },

        // Developer routes
        { path: 'scripts', element: <ScriptStudio /> },
        { path: 'workflow-builder', element: <WorkflowBuilder /> },
        { path: 'schema', element: <SchemaManager /> },
        { path: 'api-explorer', element: <ApiExplorer /> },
        { path: 'debug', element: <DebugConsole /> },

        // Assistant routes
        { path: 'chat', element: <Chat /> },
      ],
    },
  ],
  {
    basename: '/mcp',
  }
);

export function Router() {
  return <RouterProvider router={router} />;
}
