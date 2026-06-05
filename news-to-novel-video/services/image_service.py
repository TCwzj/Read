"""
图片生成服务封装
支持 Stable Diffusion WebUI API 和 DALL-E API
"""
import asyncio
import base64
from pathlib import Path
from typing import Optional

import aiohttp
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from config.settings import settings, IMAGES_DIR


class ImageService:
    """图片生成服务"""

    def __init__(self):
        self._sd_api_url = settings.SD_API_URL
        self._sd_enabled = settings.SD_API_ENABLED

    async def generate_via_sd(
        self,
        prompt: str,
        negative_prompt: str = "",
        width: int = 1920,
        height: int = 1080,
        output_path: str = "",
        seed: int = -1,
        steps: int = 30,
        cfg_scale: float = 7.0,
        sampler_name: str = "DPM++ 2M Karras",
    ) -> str:
        """
        通过Stable Diffusion WebUI API生成图片

        Args:
            prompt: 正向提示词
            negative_prompt: 负向提示词
            width: 图片宽度
            height: 图片高度
            output_path: 输出路径
            seed: 随机种子
            steps: 采样步数
            cfg_scale: CFG引导系数
            sampler_name: 采样器名称

        Returns:
            保存的图片路径
        """
        payload = {
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "width": width,
            "height": height,
            "seed": seed,
            "steps": steps,
            "cfg_scale": cfg_scale,
            "sampler_name": sampler_name,
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self._sd_api_url}/sdapi/v1/txt2img",
                json=payload,
            ) as response:
                result = await response.json()

        # 保存图片
        if output_path:
            image_data = base64.b64decode(result["images"][0])
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "wb") as f:
                f.write(image_data)
            logger.debug(f"SD图片生成完成: {output_path}")
            return output_path
        else:
            return result["images"][0]  # 返回base64

    async def generate_via_dalle(
        self,
        prompt: str,
        size: str = "1792x1024",
        quality: str = "standard",
        output_path: str = "",
    ) -> str:
        """
        通过DALL-E API生成图片

        Args:
            prompt: 提示词
            size: 图片尺寸
            quality: 图片质量 (standard/hd)
            output_path: 输出路径

        Returns:
            保存的图片路径
        """
        from openai import AsyncOpenAI

        client = AsyncOpenAI(
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_BASE_URL,
        )

        response = await client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size=size,
            quality=quality,
            n=1,
        )

        image_url = response.data[0].url

        # 下载图片
        if output_path:
            async with aiohttp.ClientSession() as session:
                async with session.get(image_url) as resp:
                    image_data = await resp.read()

            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "wb") as f:
                f.write(image_data)
            logger.debug(f"DALL-E图片生成完成: {output_path}")
            return output_path

        return image_url

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def generate_single(
        self,
        prompt: str,
        negative_prompt: str = "",
        width: int = 1920,
        height: int = 1080,
        output_path: str = "",
        seed: int = -1,
    ) -> str:
        """
        生成单张图片（自动选择可用的服务）

        Args:
            prompt: 正向提示词
            negative_prompt: 负向提示词
            width: 图片宽度
            height: 图片高度
            output_path: 输出路径
            seed: 随机种子

        Returns:
            保存的图片路径
        """
        if self._sd_enabled:
            return await self.generate_via_sd(
                prompt=prompt,
                negative_prompt=negative_prompt,
                width=width,
                height=height,
                output_path=output_path,
                seed=seed,
            )
        else:
            # 使用DALL-E
            size = "1792x1024" if width >= 1792 else "1024x1024"
            return await self.generate_via_dalle(
                prompt=prompt,
                size=size,
                output_path=output_path,
            )

    async def generate_batch(
        self,
        prompts: list[dict],
        output_dir: str = "",
        width: int = 1920,
        height: int = 1080,
        batch_size: int = 5,
    ) -> list[str]:
        """
        批量生成图片

        Args:
            prompts: 提示词列表，每条包含prompt和negative_prompt
            output_dir: 输出目录
            width: 图片宽度
            height: 图片高度
            batch_size: 每批并发数量

        Returns:
            图片路径列表
        """
        output_dir = output_dir or str(IMAGES_DIR)
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        image_paths = []
        total = len(prompts)

        # 分批处理
        for i in range(0, total, batch_size):
            batch = prompts[i : i + batch_size]
            tasks = []

            for j, prompt_data in enumerate(batch):
                idx = i + j
                output_path = str(Path(output_dir) / f"scene_{idx:04d}.png")
                task = self.generate_single(
                    prompt=prompt_data.get("prompt", ""),
                    negative_prompt=prompt_data.get("negative_prompt", ""),
                    width=width,
                    height=height,
                    output_path=output_path,
                    seed=42 + idx,
                )
                tasks.append(task)

            # 并发执行
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"图片生成失败: {result}")
                    image_paths.append("")
                else:
                    image_paths.append(result)

            logger.info(f"图片生成进度: {min(i + batch_size, total)}/{total}")

            # 避免API限流
            await asyncio.sleep(1)

        # 过滤掉失败的
        success_count = sum(1 for p in image_paths if p)
        logger.info(f"图片批量生成完成: 成功{success_count}/{total}")

        return image_paths

    def generate_batch_sync(
        self,
        prompts: list[dict],
        output_dir: str = "",
        width: int = 1920,
        height: int = 1080,
        batch_size: int = 5,
    ) -> list[str]:
        """同步版本的批量图片生成"""
        return asyncio.run(
            self.generate_batch(prompts, output_dir, width, height, batch_size)
        )


# 全局服务实例
image_service = ImageService()