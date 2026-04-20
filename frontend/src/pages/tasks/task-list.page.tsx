import { FeaturePlaceholder } from "../../components/common/feature-placeholder";

export function TaskListPage() {
  return (
    <FeaturePlaceholder
      title="任务列表页骨架"
      summary="用于验证任务页路由入口、页面命名规则和控制台布局承载能力。"
      routeKey="/tasks"
      nextModules={["任务表格", "状态筛选", "执行链路入口", "空态与错误态"]}
      ctaPath="/tasks/new"
      ctaLabel="查看新建任务占位页"
    />
  );
}
