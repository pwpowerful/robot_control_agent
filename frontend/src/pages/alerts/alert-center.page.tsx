import { FeaturePlaceholder } from "../../components/common/feature-placeholder";

export function AlertCenterPage() {
  return (
    <FeaturePlaceholder
      title="告警中心页骨架"
      summary="为高优先级安全告警、停机事件和处理状态预留前端页面结构。"
      routeKey="/alerts"
      nextModules={["告警列表", "严重级别标签", "停机事件详情", "处理状态流转"]}
    />
  );
}
