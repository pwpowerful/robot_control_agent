import { ArrowRightOutlined } from "@ant-design/icons";
import { Button, Card, Space, Tag, Typography } from "antd";
import { Link } from "react-router-dom";

type FeaturePlaceholderProps = {
  title: string;
  summary: string;
  routeKey: string;
  nextModules: string[];
  ctaPath?: string;
  ctaLabel?: string;
};

export function FeaturePlaceholder({
  title,
  summary,
  routeKey,
  nextModules,
  ctaPath,
  ctaLabel
}: FeaturePlaceholderProps) {
  return (
    <Card className="console-card feature-card">
      <Space direction="vertical" size={20} style={{ width: "100%" }}>
        <Space size={10} wrap>
          <Tag color="cyan">基础占位页</Tag>
          <Tag>{routeKey}</Tag>
        </Space>
        <div>
          <Typography.Title level={2}>{title}</Typography.Title>
          <Typography.Paragraph type="secondary">
            {summary}
          </Typography.Paragraph>
        </div>
        <div className="feature-modules">
          {nextModules.map((item) => (
            <Card key={item} size="small">
              <Typography.Text strong>{item}</Typography.Text>
            </Card>
          ))}
        </div>
        {ctaPath && ctaLabel ? (
          <Link to={ctaPath}>
            <Button type="primary" icon={<ArrowRightOutlined />}>
              {ctaLabel}
            </Button>
          </Link>
        ) : null}
      </Space>
    </Card>
  );
}
