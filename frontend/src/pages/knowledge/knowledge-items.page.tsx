import { FeaturePlaceholder } from "../../components/common/feature-placeholder";

export function KnowledgeItemsPage() {
  return (
    <FeaturePlaceholder
      title="知识条目页骨架"
      summary="为 SDK 文档、SOP 和检索元数据管理提供结构预留。"
      routeKey="/knowledge/items"
      nextModules={["知识条目列表", "元数据面板", "检索标签", "内容编辑器"]}
    />
  );
}
