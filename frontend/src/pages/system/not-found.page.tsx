import { Button, Result } from "antd";
import { Link } from "react-router-dom";

export function NotFoundPage() {
  return (
    <div className="system-page">
      <Result
        status="404"
        title="未找到页面"
        subTitle="当前路由不存在，返回前端基础骨架首页继续验证。"
        extra={
          <Link to="/tasks">
            <Button type="primary">返回任务列表占位页</Button>
          </Link>
        }
      />
    </div>
  );
}
