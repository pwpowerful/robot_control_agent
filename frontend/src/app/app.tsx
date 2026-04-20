import { App as AntApp, ConfigProvider, theme } from "antd";
import zhCN from "antd/locale/zh_CN";
import { RouterProvider } from "react-router-dom";
import { router } from "../routes/router";
import { AppShellStoreProvider } from "../stores/app-shell.store";

export function App() {
  return (
    <ConfigProvider
      locale={zhCN}
      theme={{
        algorithm: theme.defaultAlgorithm,
        token: {
          borderRadius: 18,
          colorPrimary: "#0f766e",
          colorInfo: "#0f766e",
          colorSuccess: "#2f855a",
          colorWarning: "#c27803",
          colorError: "#c94f3d",
          colorBgLayout: "#f3efe6",
          colorBgContainer: "rgba(255, 251, 243, 0.86)",
          colorTextBase: "#1f2933",
          fontFamily:
            "\"Bahnschrift\", \"Segoe UI Variable\", \"Microsoft YaHei UI\", sans-serif"
        }
      }}
    >
      <AntApp>
        <AppShellStoreProvider>
          <RouterProvider router={router} />
        </AppShellStoreProvider>
      </AntApp>
    </ConfigProvider>
  );
}
