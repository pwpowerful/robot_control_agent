import { FeaturePlaceholder } from "../../components/common/feature-placeholder";

export function TeachingSamplesPage() {
  return (
    <FeaturePlaceholder
      title="示教样本页骨架"
      summary="为后续示教样本管理、来源追踪和经验沉淀提供页面骨架。"
      routeKey="/knowledge/samples"
      nextModules={["样本列表", "版本信息", "来源标识", "样本详情抽屉"]}
    />
  );
}
