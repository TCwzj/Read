"""
LLM 服务层 - 统一的模型调用接口
支持多种后端：OpenAI, Azure, Anthropic, Gemini, Ollama, 本地 API
"""
import json
import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List, Union
from config.settings import LLMConfig

logger = logging.getLogger(__name__)


class BaseLLM(ABC):
    """LLM 基类"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.model_name = config.get("model_name", "gpt-4o")
        self.temperature = config.get("temperature", 0.7)
        self.max_tokens = config.get("max_tokens", 4096)
    
    @abstractmethod
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """生成文本回复"""
        pass
    
    @abstractmethod
    def generate_json(self, prompt: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        """生成结构化 JSON 输出"""
        pass
    
    @abstractmethod
    def generate_with_tools(self, prompt: str, tools: List[Dict[str, Any]]) -> Dict[str, Any]:
        """使用工具调用功能"""
        pass


class OpenAILLM(BaseLLM):
    """OpenAI 兼容 API 实现 (支持 OpenAI, Ollama, 通义千问等)"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get("api_key", "")
        self.api_base = config.get("api_base", "https://api.openai.com/v1")
        
        # 动态导入 openai 库
        try:
            from openai import OpenAI
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.api_base if self.api_base else None
            )
            logger.info(f"OpenAI 客户端初始化成功，端点：{self.api_base}")
        except ImportError:
            logger.warning("openai 库未安装，使用 HTTP 直接调用")
            self.client = None
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        if self.client:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            return response.choices[0].message.content
        else:
            # HTTP 直接调用
            import requests
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            data = {
                "model": self.model_name,
                "messages": messages,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens
            }
            resp = requests.post(f"{self.api_base}/chat/completions", headers=headers, json=data)
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]
    
    def generate_json(self, prompt: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        """生成 JSON 输出"""
        system_prompt = f"""你是一个 JSON 生成助手。请严格按照以下 JSON Schema 格式输出：
{json.dumps(schema, ensure_ascii=False, indent=2)}

注意：
1. 只输出纯 JSON，不要有任何其他内容
2. 不要包含 Markdown 格式（如 ```json）
3. 确保 JSON 格式正确"""
        
        response = self.generate(prompt, system_prompt)
        # 清理可能的 Markdown 标记
        response = response.strip().replace("```json", "").replace("```", "").strip()
        return json.loads(response)
    
    def generate_with_tools(self, prompt: str, tools: List[Dict[str, Any]]) -> Dict[str, Any]:
        """使用工具调用"""
        messages = [
            {"role": "user", "content": prompt}
        ]
        
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            tools=tools,
            tool_choice="auto"
        )
        
        result = {
            "content": response.choices[0].message.content,
            "tool_calls": []
        }
        
        if response.choices[0].message.tool_calls:
            for tc in response.choices[0].message.tool_calls:
                result["tool_calls"].append({
                    "name": tc.function.name,
                    "arguments": json.loads(tc.function.arguments)
                })
        
        return result


class AnthropicLLM(BaseLLM):
    """Anthropic Claude 实现"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get("api_key", "")
        
        try:
            from anthropic import Anthropic
            self.client = Anthropic(api_key=self.api_key)
        except ImportError:
            self.client = None
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        if self.client:
            response = self.client.messages.create(
                model=self.model_name,
                max_tokens=self.max_tokens,
                system=system_prompt or "",
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        else:
            import requests
            headers = {
                "x-api-key": self.api_key,
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01"
            }
            data = {
                "model": self.model_name,
                "max_tokens": self.max_tokens,
                "system": system_prompt or "",
                "messages": [{"role": "user", "content": prompt}]
            }
            resp = requests.post("https://api.anthropic.com/v1/messages", headers=headers, json=data)
            resp.raise_for_status()
            return resp.json()["content"][0]["text"]
    
    def generate_json(self, prompt: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        system_prompt = f"""你是一个 JSON 生成助手。请严格按照以下 JSON Schema 格式输出：
{json.dumps(schema, ensure_ascii=False, indent=2)}

注意：只输出纯 JSON，不要有任何其他内容。"""
        
        response = self.generate(prompt, system_prompt)
        response = response.strip().replace("```json", "").replace("```", "").strip()
        return json.loads(response)
    
    def generate_with_tools(self, prompt: str, tools: List[Dict[str, Any]]) -> Dict[str, Any]:
        # Anthropic 的工具调用支持
        raise NotImplementedError("工具调用功能待实现")


class OllamaLLM(BaseLLM):
    """Ollama 本地模型实现"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_base = config.get("api_base", "http://localhost:11434")
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        import requests
        
        url = f"{self.api_base}/api/chat"
        data = {
            "model": self.model_name,
            "messages": [],
            "stream": False
        }
        
        if system_prompt:
            data["messages"].append({"role": "system", "content": system_prompt})
        data["messages"].append({"role": "user", "content": prompt})
        
        resp = requests.post(url, json=data)
        resp.raise_for_status()
        return resp.json()["message"]["content"]
    
    def generate_json(self, prompt: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        system_prompt = f"请输出 JSON 格式，符合以下 Schema:\n{json.dumps(schema)}"
        response = self.generate(prompt, system_prompt)
        return json.loads(response.strip())
    
    def generate_with_tools(self, prompt: str, tools: List[Dict[str, Any]]) -> Dict[str, Any]:
        raise NotImplementedError("Ollama 工具调用待实现")


class LocalAPILLM(BaseLLM):
    """通用本地 API 实现 (用于 vLLM, LocalAI 等)"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_base = config.get("api_base", "http://localhost:8000")
        self.api_key = config.get("api_key", "not-needed")
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        import requests
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        data = {
            "model": self.model_name,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }
        
        resp = requests.post(f"{self.api_base}/v1/chat/completions", headers=headers, json=data)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]
    
    def generate_json(self, prompt: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        system_prompt = f"请输出 JSON 格式：{json.dumps(schema)}"
        response = self.generate(prompt, system_prompt)
        return json.loads(response.strip())
    
    def generate_with_tools(self, prompt: str, tools: List[Dict[str, Any]]) -> Dict[str, Any]:
        raise NotImplementedError


# LLM 工厂
PROVIDER_MAP = {
    "openai": OpenAILLM,
    "azure": OpenAILLM,  # Azure 使用 OpenAI 兼容接口
    "anthropic": AnthropicLLM,
    "ollama": OllamaLLM,
    "localapi": LocalAPILLM,
}


def get_llm(config: Optional[Dict[str, Any]] = None) -> BaseLLM:
    """
    获取 LLM 实例
    
    Args:
        config: 配置字典，如果不传则使用默认配置
    
    Returns:
        LLM 实例
    """
    if config is None:
        config = LLMConfig.get_config()
    
    provider = config.get("provider", "openai").lower()
    
    if provider not in PROVIDER_MAP:
        logger.warning(f"不支持的提供商：{provider}，使用 OpenAI 兼容接口")
        provider = "openai"
    
    llm_class = PROVIDER_MAP[provider]
    return llm_class(config)


# 便捷函数
def llm_generate(prompt: str, system_prompt: Optional[str] = None, config: Optional[Dict] = None) -> str:
    """快捷生成文本"""
    llm = get_llm(config)
    return llm.generate(prompt, system_prompt)


def llm_generate_json(prompt: str, schema: Dict[str, Any], config: Optional[Dict] = None) -> Dict:
    """快捷生成 JSON"""
    llm = get_llm(config)
    return llm.generate_json(prompt, schema)