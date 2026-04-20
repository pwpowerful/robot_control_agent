import { Button, Card, Input, Space, Tag, Typography } from "antd";

export function LoginPage() {
  return (
    <div className="auth-page">
      <Card className="auth-card console-card">
        <Space direction="vertical" size={20} style={{ width: "100%" }}>
          <Tag color="processing">路由占位</Tag>
          <div>
            <Typography.Title level={1}>登录页骨架</Typography.Title>
            <Typography.Paragraph type="secondary">
              当前只验证页面入口与命名约定，不实现真实会话逻辑。
            </Typography.Paragraph>
          </div>
          <Input placeholder="用户名" size="large" disabled />
          <Input.Password placeholder="密码" size="large" disabled />
          <Button type="primary" size="large" block disabled>
            登录功能将在后续步骤接入
          </Button>
        </Space>
      </Card>
    </div>
  );
}
