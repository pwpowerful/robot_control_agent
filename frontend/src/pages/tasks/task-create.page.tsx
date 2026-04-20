import { FeaturePlaceholder } from "../../components/common/feature-placeholder";

export function TaskCreatePage() {
  return (
    <FeaturePlaceholder
      title="新建任务页骨架"
      summary="当前只保留页面承载位，后续步骤再接入自然语言任务输入、结构化辅助字段和表单校验。"
      routeKey="/tasks/new"
      nextModules={["任务表单", "结构化辅助字段", "提交状态", "校验反馈"]}
      ctaPath="/tasks/demo-task"
      ctaLabel="查看任务详情占位页"
    />
  );
}
