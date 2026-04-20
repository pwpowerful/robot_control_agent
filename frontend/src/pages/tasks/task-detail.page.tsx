import { useParams } from "react-router-dom";
import { FeaturePlaceholder } from "../../components/common/feature-placeholder";

export function TaskDetailPage() {
  const { taskId = ":taskId" } = useParams();

  return (
    <FeaturePlaceholder
      title="任务详情页骨架"
      summary={`当前仅验证动态路由可用，示例任务标识为 ${taskId}。`}
      routeKey="/tasks/:taskId"
      nextModules={[
        "原始指令展示",
        "执行计划步骤",
        "校验结果摘要",
        "执行结果与视觉复检"
      ]}
    />
  );
}
