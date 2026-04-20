import { FeaturePlaceholder } from "../../components/common/feature-placeholder";

export function AuditLogPage() {
  return (
    <FeaturePlaceholder
      title="审计日志页骨架"
      summary="为后续任务链路追溯、时间筛选和事件明细展示保留页面位置。"
      routeKey="/audit"
      nextModules={["审计检索", "事件时间线", "任务维度过滤", "原始记录查看"]}
    />
  );
}
