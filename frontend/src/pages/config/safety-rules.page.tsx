import { FeaturePlaceholder } from "../../components/common/feature-placeholder";

export function SafetyRulesPage() {
  return (
    <FeaturePlaceholder
      title="安全规则页骨架"
      summary="为工作禁区、安全阈值和停机规则的后续维护预留页面空间。"
      routeKey="/config/safety-rules"
      nextModules={["禁区配置", "阈值配置", "规则版本", "变更审计"]}
    />
  );
}
