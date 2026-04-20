import { MenuFoldOutlined, MenuUnfoldOutlined } from "@ant-design/icons";
import { Button, Layout, Menu, Space, Tag, Typography } from "antd";
import { Link, Outlet, useLocation } from "react-router-dom";
import { consoleNavigationItems } from "../../app/console-navigation";
import { useAppShellStore } from "../../stores/app-shell.store";

const { Header, Sider, Content } = Layout;

export function ConsoleShell() {
  const location = useLocation();
  const { collapsed, toggleCollapsed } = useAppShellStore();
  const selectedKey =
    consoleNavigationItems
      .filter(
        (item) =>
          location.pathname === item.path ||
          location.pathname.startsWith(`${item.path}/`)
      )
      .sort((left, right) => right.path.length - left.path.length)[0]?.key ?? "tasks";

  return (
    <Layout className="console-root">
      <Sider
        breakpoint="lg"
        collapsedWidth={84}
        collapsible
        trigger={null}
        collapsed={collapsed}
        className="console-sider"
      >
        <div className="console-brand">
          <Typography.Text className="console-brand-title">
            RCA
          </Typography.Text>
          {!collapsed ? (
            <Typography.Text type="secondary">
              Robot Control Agent
            </Typography.Text>
          ) : null}
        </div>
        <Menu
          mode="inline"
          selectedKeys={[selectedKey]}
          items={consoleNavigationItems
            .filter((item) => item.key !== "login")
            .map((item) => ({
              key: item.key,
              icon: item.icon,
              label: <Link to={item.path}>{item.label}</Link>
            }))}
        />
      </Sider>
      <Layout>
        <Header className="console-header">
          <Space size={16}>
            <Button
              type="text"
              icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
              onClick={toggleCollapsed}
              aria-label="切换导航"
            />
            <div>
              <Typography.Text className="console-header-kicker">
                智能机械臂控制台
              </Typography.Text>
              <Typography.Title level={4} style={{ margin: 0 }}>
                前端基础工程骨架
              </Typography.Title>
            </div>
          </Space>
          <Space size={12} wrap>
            <Tag color="processing">步骤 04</Tag>
            <Tag>React 19</Tag>
            <Tag>Vite 8</Tag>
            <Tag>Ant Design</Tag>
          </Space>
        </Header>
        <Content className="console-content">
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
}
