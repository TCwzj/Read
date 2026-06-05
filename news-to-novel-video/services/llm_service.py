"""
LLM服务封装
基于LangChain + OpenAI API
"""
import json
from pathlib import Path
from typing import Optional

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from loguru import logger

from config.settings import settings, PROMPTS_DIR


class LLMService:
    """LLM调用服务"""

    def __init__(self):
        self._client: Optional[ChatOpenAI] = None

    @property
    def client(self) -> ChatOpenAI:
        """懒加载LLM客户端"""
        if self._client is None:
            self._client = ChatOpenAI(
                api_key=settings.OPENAI_API_KEY,
                base_url=settings.OPENAI_BASE_URL,
                model=settings.OPENAI_MODEL,
                temperature=settings.LLM_TEMPERATURE,
                max_tokens=settings.LLM_MAX_TOKENS,
            )
        return self._client

    def invoke(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> str:
        """
        调用LLM生成文本

        Args:
            prompt: 用户提示词
            system_prompt: 系统提示词
            temperature: 温度参数（覆盖默认值）

        Returns:
            LLM生成的文本
        """
        messages = []
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        messages.append(HumanMessage(content=prompt))

        client = self.client
        if temperature is not None:
            client = self.client.bind(temperature=temperature)

        try:
            response = client.invoke(messages)
            logger.debug(f"LLM调用成功，输出长度: {len(response.content)}")
            return response.content
        except Exception as e:
            logger.error(f"LLM调用失败: {e}")
            raise

    def invoke_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
    ) -> dict | list:
        """
        调用LLM并解析JSON输出

        Args:
            prompt: 用户提示词
            system_prompt: 系统提示词

        Returns:
            解析后的JSON对象
        """
        response = self.invoke(prompt, system_prompt)

        # 尝试从响应中提取JSON
        try:
            # 直接解析
            return json.loads(response)
        except json.JSONDecodeError:
            pass

        # 尝试提取 ```json ... ``` 块
        import re
        json_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        # 尝试提取花括号或方括号内容
        for pattern in [r"\{.*\}", r"\[.*\]"]:
            match = re.search(pattern, response, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group())
                except json.JSONDecodeError:
                    continue

        logger.warning(f"无法解析LLM输出的JSON，返回原始文本")
        return {"raw_response": response}

    def load_prompt_template(self, template_name: str) -> str:
        """
        加载提示词模板

        Args:
            template_name: 模板名称（不含路径和扩展名）

        Returns:
            模板内容
        """
        template_path = PROMPTS_DIR / f"{template_name}.txt"
        if not template_path.exists():
            raise FileNotFoundError(f"提示词模板不存在: {template_path}")
        return template_path.read_text(encoding="utf-8")

    def invoke_with_template(
        self,
        template_name: str,
        variables: dict,
        system_prompt: Optional[str] = None,
    ) -> str:
        """
        使用模板调用LLM

        Args:
            template_name: 模板名称
            variables: 模板变量
            system_prompt: 系统提示词

        Returns:
            LLM生成的文本
        """
        template = self.load_prompt_template(template_name)
        prompt = template.format(**variables)
        return self.invoke(prompt, system_prompt)

    async def ainvoke(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
    ) -> str:
        """
        异步调用LLM

        Args:
            prompt: 用户提示词
            system_prompt: 系统提示词

        Returns:
            LLM生成的文本
        """
        messages = []
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        messages.append(HumanMessage(content=prompt))

        try:
            response = await self.client.ainvoke(messages)
            return response.content
        except Exception as e:
            logger.error(f"LLM异步调用失败: {e}")
            raise


# 全局服务实例
llm_service = LLMService()