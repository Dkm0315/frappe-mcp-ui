/**
 * React Router Configuration
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

const router = createBrowserRouter(
  [
    {
      path: '/',
      element: <AppShell />,
      children: [
        {
          index: true,
          element: <Dashboard />,
        },
        {
          path: 'tools',
          element: <Tools />,
        },
        {
          path: 'workflows',
          element: <Workflows />,
        },
        {
          path: 'history',
          element: <History />,
        },
        {
          path: 'credits',
          element: <Credits />,
        },
        {
          path: 'discovery',
          element: <Discovery />,
        },
        {
          path: 'settings',
          element: <Settings />,
        },
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

