import { createBrowserRouter, Navigate } from "react-router-dom";
import { ConsoleShell } from "../components/shell/console-shell";

export const router = createBrowserRouter([
  {
    path: "/",
    element: <Navigate to="/tasks" replace />
  },
  {
    path: "/login",
    async lazy() {
      const module = await import("../pages/auth/login.page");
      return { Component: module.LoginPage };
    }
  },
  {
    path: "/",
    element: <ConsoleShell />,
    children: [
      {
        path: "tasks",
        async lazy() {
          const module = await import("../pages/tasks/task-list.page");
          return { Component: module.TaskListPage };
        }
      },
      {
        path: "tasks/new",
        async lazy() {
          const module = await import("../pages/tasks/task-create.page");
          return { Component: module.TaskCreatePage };
        }
      },
      {
        path: "tasks/:taskId",
        async lazy() {
          const module = await import("../pages/tasks/task-detail.page");
          return { Component: module.TaskDetailPage };
        }
      },
      {
        path: "alerts",
        async lazy() {
          const module = await import("../pages/alerts/alert-center.page");
          return { Component: module.AlertCenterPage };
        }
      },
      {
        path: "audit",
        async lazy() {
          const module = await import("../pages/audit/audit-log.page");
          return { Component: module.AuditLogPage };
        }
      },
      {
        path: "knowledge/items",
        async lazy() {
          const module = await import("../pages/knowledge/knowledge-items.page");
          return { Component: module.KnowledgeItemsPage };
        }
      },
      {
        path: "knowledge/samples",
        async lazy() {
          const module = await import("../pages/knowledge/teaching-samples.page");
          return { Component: module.TeachingSamplesPage };
        }
      },
      {
        path: "config/robot",
        async lazy() {
          const module = await import("../pages/config/robot-config.page");
          return { Component: module.RobotConfigPage };
        }
      },
      {
        path: "config/safety-rules",
        async lazy() {
          const module = await import("../pages/config/safety-rules.page");
          return { Component: module.SafetyRulesPage };
        }
      }
    ]
  },
  {
    path: "*",
    async lazy() {
      const module = await import("../pages/system/not-found.page");
      return { Component: module.NotFoundPage };
    }
  }
]);
