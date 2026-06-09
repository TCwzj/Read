# Skills - 提示词模板集合

每个 Skill 都是一个提示词模板，供智能体使用 LLM 完成任务。

## Skill 列表

| Skill 名称 | 文件 | 用途 | 输入 | 输出 |
|-----------|------|------|------|------|
| `scrape_news` | `scrape_news.md` | 辅助解析新闻页面 | HTML 内容 | 结构化新闻数据 |
| `remove_pii` | `remove_pii.md` | PII 脱敏 | 原始文本 | 脱敏后文本 + 替换记录 |
| `rewrite_novel` | `rewrite_novel.md` | 小说化改写 | 脱敏新闻 | 小说体裁文本 |
| `split_scenes` | `split_scenes.md` | 分镜拆分 | 小说文本 | 分镜列表 |
| `optimize_prompt` | `optimize_prompt.md` | 提示词优化 | 画面描述 | 优化后的英文提示词 |
| `generate_audio` | `generate_audio.md` | TTS 参数生成 | 旁白文本 | TTS 配置参数 |
| `generate_images` | `generate_images.md` | 图片质量检查 | 生成的图片 | 质量评分 |
| `compose_video` | `compose_video.md` | 转场风格决策 | 情绪标签 | 转场参数 |
| `style_consistency` | `style_consistency.md` | 风格一致性检查 | 参考图 + 新图 | 一致性评分 |
| `post_process` | `post_process.md` | 片头片尾文案 | 故事概要 | 标题/简介 |

## Skill 模板结构

每个 Skill 模板包含以下部分：

```markdown
# Skill 名称

## 角色设定 (System Prompt)
你是一位...

## 任务描述
请完成以下任务...

## 输入格式
```json
{
  "input_field": "类型说明"
}
```

## 输出格式 (JSON Schema)
```json
{
  "type": "object",
  "properties": {
    "output_field": "类型说明"
  }
}
```

## 示例
输入示例 → 输出示例
```

## 使用方式

智能体加载 Skill 模板：

```python
from agents.base_agent import BaseAgent

agent = BaseAgent()

# 加载 Skill 模板
with open("skills/remove_pii.md") as f:
    skill_template = f.read()

# 使用 Skill 执行任务
result = agent.think_with_skill(
    skill_template=skill_template,
    input_data={"text": "张三在北京市朝阳区..."}
)
```

## 提示词设计原则

1. **角色明确** - 定义专家角色
2. **任务清晰** - 明确说明要做什么
3. **格式约束** - 使用 JSON Schema 规范输出
4. **示例驱动** - 提供 Few-Shot 示例
5. **边界处理** - 说明特殊情况的处理方式