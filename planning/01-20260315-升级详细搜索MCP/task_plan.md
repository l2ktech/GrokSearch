# 升级详细搜索 MCP

## 目标
为 GrokSearch MCP 增加一个可直接返回详细、全面搜索结果的新高层工具，并完成本地验证与回归测试，避免用户只拿到碎片化 snippet。

## Planning 查重记录
- 检索时间：2026-03-15 08:10 CST
- 检索范围：仓库根目录与 `planning/`
- 检索关键词：`deep_search`、`research_search`、`详细搜索`、`全面搜索`、`search_and_fetch`
- 结果：未发现同类任务或现成实现
- 决策：新建本任务目录执行修复与升级

## 阶段清单

### [x] 阶段1：查重与建档
- [x] 检查现有仓库是否已有同类工具
- [x] 创建 planning 任务文件

### [x] 阶段2：方案设计
- [x] 确定新工具接口（参数/输出）
- [x] 确定内部编排（search -> fetch -> synthesis）

### [x] 阶段3：实现与文档
- [x] 修改 MCP 代码
- [x] 更新 README / 使用说明

### [x] 阶段4：验证与发布
- [x] 本地功能测试
- [x] 重启当前运行服务并验证 tools/list
- [x] 做一次真实查询 smoke test

## 错误日志
- [2026-03-15] `.venv` 中未安装 `pytest`，直接执行 `./.venv/bin/python -m pytest -q` 失败 -> 改用 `uv run --extra dev pytest -q` 完成测试。

## 进度
- 当前：任务完成，`deep_search` 已上线并通过真实调用验证
- 下一步：根据实际使用反馈继续优化抓取数量、提示词和输出结构
