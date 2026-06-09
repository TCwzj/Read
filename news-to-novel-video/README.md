# 新闻转小说视频系统

> 基于大模型和智能体协作的自动化新闻处理系统
> 从社会新闻 → 小说化改写 → 音频/图片生成 → 视频合成

## 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                    Orchestrator Agent (编排智能体)                 │
│                     负责整体流程调度和状态管理                      │
└───────────┬──────────────────────────────────────────┬──────────┘
            │                                          │
    ┌───────▼───────┐                          ┌───────▼───────┐
    │  Processor    │                          │   Media       │
    │   Agent       │                          │   Agent       │
    │  (处理智能体)  │                          │  (媒体智能体)   │
    │               │                          │               │
    │ - 脱敏        │                          │ - TTS 音频     │
    │ - 小说改写    │                          │ - AI 图片      │
    │ - 分镜拆分    │                          │               │
    └───────────────┘                          └───────────────┘
                                                        │
┌───────────────────────────────────────────────────────▼───────┐
│                    Composer Agent (合成智能体)                   │
│                     图片 + 音频 → 视频合成                       │
└───────────────────────────────────────────────────────────────┘
```

## 核心特性

### 🔌 灵活的大模型配置

支持多种 LLM 后端，可通过环境变量配置：

| 提供商 | 说明 | 配置示例 |
|--------|------|----------|
| OpenAI | GPT-4o 等 | `LLM_PROVIDER=openai` |
| Azure | Azure OpenAI | `LLM_PROVIDER=azure` |
| Anthropic | Claude 系列 | `LLM_PROVIDER=anthropic` |
| Ollama | 本地模型 | `LLM_PROVIDER=ollama` |
| LocalAPI | 兼容 OpenAI 的 API | `LLM_PROVIDER=localapi` |

### 🤖 智能体协作

- **Orchestrator Agent**: 总指挥，负责流水线调度
- **Processor Agent**: 编剧，负责脱敏、改写、分镜
- **Media Agent**: 制作人，负责音频和图片生成
- **Composer Agent**: 剪辑师，负责视频合成

### 🛠️ Skill 模块化

每个处理步骤都是独立的 Skill，可复用、可替换：

1. `scrape_news` - 新闻抓取
2. `remove_pii` - LLM 智能脱敏
3. `rewrite_novel` - 小说化改写
4. `split_scenes` - 分镜拆分
5. `optimize_prompt` - 提示词优化
6. `generate_audio` - TTS 语音合成
7. `generate_images` - AI 图片生成
8. `compose_video` - 视频合成
9. `style_consistency` - 风格一致性控制
10. `post_process` - 视频后处理

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env` 并填写配置：

```bash
# 大模型配置
LLM_PROVIDER=openai
LLM_API_KEY=your-api-key-here
LLM_MODEL_NAME=gpt-4o

# TTS 配置
TTS_PROVIDER=edge

# 图片生成配置
IMAGE_PROVIDER=stable_diffusion
IMAGE_API_BASE=http://localhost:7860
```

### 3. 运行

```bash
python main.py
```

或者作为模块使用：

```python
from agents.orchestrator import OrchestratorAgent

orchestrator = OrchestratorAgent()
result = orchestrator.execute({
    "count": 5,
    "style": "realism"
})
```

## 配置说明

### LLM 配置

```bash
# OpenAI / 兼容 API
LLM_PROVIDER=openai
LLM_API_KEY=sk-xxx
LLM_API_BASE=https://api.openai.com/v1
LLM_MODEL_NAME=gpt-4o

# Ollama 本地模型
LLM_PROVIDER=ollama
LLM_API_BASE=http://localhost:11434
LLM_MODEL_NAME=qwen:72b

# 通义千问 (阿里云)
LLM_PROVIDER=openai  # 使用兼容模式
LLM_API_KEY=sk-xxx
LLM_API_BASE=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_MODEL_NAME=qwen-max
```

### TTS 配置

```bash
# Edge TTS (免费)
TTS_PROVIDER=edge
TTS_VOICE=zh-CN-XiaoxiaoNeural

# Azure TTS
TTS_PROVIDER=azure
TTS_API_KEY=xxx
TTS_VOICE=zh-CN-XiaoxiaoNeural
```

### 图片生成配置

```bash
# Stable Diffusion WebUI
IMAGE_PROVIDER=stable_diffusion
IMAGE_API_BASE=http://localhost:7860

# ComfyUI
IMAGE_PROVIDER=comfyui
IMAGE_API_BASE=http://localhost:8188

# DALL-E 3
IMAGE_PROVIDER=dall-e
IMAGE_API_KEY=sk-xxx
```

## 项目结构

```
news-to-novel-video/
├── README.md              # 本文件
├── .env.example           # 环境变量模板
├── requirements.txt       # Python 依赖
├── main.py               # 主入口
│
├── config/               # 配置目录
│   ├── settings.py       # 全局配置
│   └── prompts/          # LLM 提示词模板
│
├── agents/               # 智能体
│   ├── base_agent.py     # 智能体基类
│   ├── orchestrator.py   # 编排智能体
│   ├── processor.py      # 处理智能体
│   ├── media.py          # 媒体智能体
│   └── composer.py       # 合成智能体
│
├── services/             # 服务层
│   ├── llm_service.py    # LLM 调用服务
│   ├── tts_service.py    # TTS 服务
│   ├── image_service.py  # 图片生成服务
│   └── video_service.py  # 视频处理服务
│
├── skills/               # 技能模块
│   ├── scrape_news.py    # 新闻抓取
│   ├── remove_pii.py     # PII 脱敏
│   ├── rewrite_novel.py  # 小说改写
│   ├── split_scenes.py   # 分镜拆分
│   ├── optimize_prompt.py# 提示词优化
│   ├── generate_audio.py # 音频生成
│   ├── generate_images.py# 图片生成
│   ├── compose_video.py  # 视频合成
│   └── ...
│
├── models/               # 数据模型
│   └── schemas.py        # Pydantic 模型
│
├── pipeline/             # 流水线定义
│   └── workflow.py       # 工作流
│
├── storage/              # 存储目录
│   ├── images/           # 生成的图片
│   ├── audio/            # 生成的音频
│   ├── video/            # 生成的视频
│   └── temp/             # 临时文件
│
└── tests/                # 测试
    └── test_skills.py    # Skill 测试
```

## API 参考

### OrchestratorAgent

```python
orchestrator = OrchestratorAgent()

# 执行完整流水线
result = orchestrator.execute({
    "count": 10,          # 抓取新闻条数
    "category": "society",# 新闻分类
    "style": "realism"    # 小说风格
})

# 获取状态
status = orchestrator.get_status()
```

### 直接使用 Skill

```python
from skills.remove_pii import remove_pii
from skills.rewrite_novel import rewrite_as_novel

# 脱敏
result = remove_pii(text="张三在北京市朝阳区...")

# 小说改写
result = rewrite_as_novel(text="...", style="suspense")
```

## 开发路线

- [ ] 完善所有 Skill 的 LLM 集成
- [ ] 添加 Web 管理界面
- [ ] 支持批量并行处理
- [ ] 添加内容审核过滤
- [ ] 支持更多 TTS 和图片生成服务

## License

MIT