"""
智能体基类

所有智能体都继承自此基类，提供通用的 LLM 调用和 Skill 模板加载功能。
"""

import json
import re
from typing import Any, Dict, List, Optional
from services.llm_service import LLMService


class BaseAgent:
    """智能体基类"""

    def __init__(self, name: str, llm_service: Optional[LLMService] = None):
        """
        初始化智能体

        Args:
            name: 智能体名称
            llm_service: LLM 服务实例，如果不提供则创建默认实例
        """
        self.name = name
        self.llm = llm_service or LLMService()
        self._system_prompt = ""

    def set_system_prompt(self, prompt: str) -> "BaseAgent":
        """
        设置系统提示词

        Args:
            prompt: 系统提示词

        Returns:
            self
        """
        self._system_prompt = prompt
        return self

    def think(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        使用 LLM 进行思考，返回文本响应

        Args:
            prompt: 用户提示
            system_prompt: 可选的系统提示词覆盖

        Returns:
            LLM 的文本响应
        """
        messages = []

        # 添加系统提示
        sys_prompt = system_prompt or self._system_prompt
        if sys_prompt:
            messages.append({"role": "system", "content": sys_prompt})

        # 添加用户提示
        messages.append({"role": "user", "content": prompt})

        # 调用 LLM
        response = self.llm.chat(messages)
        return response

    def think_with_skill(
        self,
        skill_template: str,
        input_data: Dict[str, Any],
        system_prompt: Optional[str] = None,
    ) -> str:
        """
        使用 Skill 模板进行思考

        Args:
            skill_template: Skill 提示词模板
            input_data: 输入数据
            system_prompt: 可选的系统提示词覆盖

        Returns:
            LLM 的文本响应
        """
        # 构建完整的提示词
        prompt = self._format_template(skill_template, input_data)

        return self.think(prompt, system_prompt)

    def think_json(
        self,
        prompt: str,
        output_schema: Optional[Dict] = None,
        system_prompt: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        使用 LLM 进行思考，返回 JSON 响应

        Args:
            prompt: 用户提示
            output_schema: 期望的输出 JSON Schema
            system_prompt: 可选的系统提示词覆盖

        Returns:
            解析后的 JSON 数据
        """
        # 构建提示词，要求输出 JSON
        json_prompt = f"""{prompt}

请严格按照以下 JSON 格式输出，不要包含其他内容：
{json.dumps(output_schema, ensure_ascii=False, indent=2) if output_schema else "{}"}
"""

        messages = []

        # 添加系统提示
        sys_prompt = system_prompt or self._system_prompt or "你是一个精确的 JSON 输出助手。请只输出 JSON 格式的数据，不要包含任何其他解释。"
        if sys_prompt:
            messages.append({"role": "system", "content": sys_prompt})

        messages.append({"role": "user", "content": json_prompt})

        # 调用 LLM
        response = self.llm.chat(messages)

        # 解析 JSON
        return self._parse_json_response(response)

    def think_with_skill_json(
        self,
        skill_template: str,
        input_data: Dict[str, Any],
        output_schema: Optional[Dict] = None,
        system_prompt: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        使用 Skill 模板进行思考，返回 JSON 响应

        Args:
            skill_template: Skill 提示词模板
            input_data: 输入数据
            output_schema: 期望的输出 JSON Schema
            system_prompt: 可选的系统提示词覆盖

        Returns:
            解析后的 JSON 数据
        """
        # 从模板中提取输出格式说明
        schema_from_template = self._extract_json_schema(skill_template)
        if schema_from_template and not output_schema:
            output_schema = schema_from_template

        # 构建完整的提示词
        prompt = self._format_template(skill_template, input_data)

        # 添加 JSON 输出要求
        if output_schema:
            prompt += f"\n\n请严格按照以下 JSON 格式输出：\n{json.dumps(output_schema, ensure_ascii=False, indent=2)}"

        return self.think_json(prompt, output_schema, system_prompt)

    def _format_template(self, template: str, input_data: Dict[str, Any]) -> str:
        """
        格式化模板，替换输入数据

        Args:
            template: 模板字符串
            input_data: 输入数据

        Returns:
            格式化后的提示词
        """
        # 简单的占位符替换
        # 支持 {key} 格式的占位符
        result = template
        for key, value in input_data.items():
            placeholder = "{" + key + "}"
            if placeholder in result:
                result = result.replace(placeholder, str(value))

        # 如果没有占位符，将输入数据以 JSON 形式追加
        if result == template:
            result += f"\n\n输入数据:\n{json.dumps(input_data, ensure_ascii=False, indent=2)}"

        return result

    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """
        从 LLM 响应中解析 JSON

        Args:
            response: LLM 的原始响应

        Returns:
            解析后的 JSON 数据

        Raises:
            ValueError: 如果无法解析 JSON
        """
        # 清理响应，提取 JSON 部分
        text = response.strip()

        # 尝试直接解析
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # 尝试提取代码块中的 JSON
        code_block_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        if code_block_match:
            try:
                return json.loads(code_block_match.group(1))
            except json.JSONDecodeError:
                pass

        # 尝试提取第一个和最后一个大括号之间的内容
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            try:
                return json.loads(text[start:end])
            except json.JSONDecodeError:
                pass

        # 无法解析
        raise ValueError(f"无法解析 JSON 响应：{response}")

    def _extract_json_schema(self, template: str) -> Optional[Dict]:
        """
        从模板中提取 JSON Schema

        Args:
            template: Skill 模板

        Returns:
            提取的 JSON Schema，如果未找到则返回 None
        """
        # 查找"输出格式"部分
        schema_match = re.search(
            r"输出格式.*?```(?:json)?\s*(\{.*?\})\s*```",
            template,
            re.DOTALL | re.IGNORECASE,
        )

        if schema_match:
            try:
                return json.loads(schema_match.group(1))
            except json.JSONDecodeError:
                pass

        return None