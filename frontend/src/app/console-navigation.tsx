import {
  AlertOutlined,
  AuditOutlined,
  LoginOutlined,
  ProfileOutlined,
  SafetyCertificateOutlined,
  SettingOutlined,
  SnippetsOutlined,
  ToolOutlined
} from "@ant-design/icons";
import type { ReactNode } from "react";

export type ConsoleNavigationItem = {
  key: string;
  label: string;
  path: string;
  icon: ReactNode;
};

export const consoleNavigationItems: ConsoleNavigationItem[] = [
  {
    key: "login",
    label: "登录",
    path: "/login",
    icon: <LoginOutlined />
  },
  {
    key: "tasks",
    label: "任务列表",
    path: "/tasks",
    icon: <ProfileOutlined />
  },
  {
    key: "task-create",
    label: "新建任务",
    path: "/tasks/new",
    icon: <ToolOutlined />
  },
  {
    key: "alerts",
    label: "告警中心",
    path: "/alerts",
    icon: <AlertOutlined />
  },
  {
    key: "audit",
    label: "审计日志",
    path: "/audit",
    icon: <AuditOutlined />
  },
  {
    key: "knowledge-items",
    label: "知识条目",
    path: "/knowledge/items",
    icon: <SnippetsOutlined />
  },
  {
    key: "knowledge-samples",
    label: "示教样本",
    path: "/knowledge/samples",
    icon: <SnippetsOutlined />
  },
  {
    key: "robot-config",
    label: "机械臂配置",
    path: "/config/robot",
    icon: <SettingOutlined />
  },
  {
    key: "safety-rules",
    label: "安全规则",
    path: "/config/safety-rules",
    icon: <SafetyCertificateOutlined />
  }
];
