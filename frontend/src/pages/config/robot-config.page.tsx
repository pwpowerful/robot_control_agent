import { FeaturePlaceholder } from "../../components/common/feature-placeholder";

export function RobotConfigPage() {
  return (
    <FeaturePlaceholder
      title="机械臂配置页骨架"
      summary="为管理员配置机器人连接、工作空间和设备参数提供布局边界。"
      routeKey="/config/robot"
      nextModules={["连接参数", "工作空间参数", "激活配置", "变更记录"]}
    />
  );
}
