import base64
from dataclasses import dataclass
from typing import Any

import httpx
from openai import AsyncOpenAI

from bot.settings import Settings, get_settings


@dataclass(frozen=True)
class GeneratedAsset:
    kind: str
    url: str
    raw: dict[str, Any]


class AgnesClient:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()
        self.client = AsyncOpenAI(
            api_key=self.settings.agnes_api_key or "missing-key",
            base_url=self.settings.agnes_base_url,
        )

    def configured(self) -> bool:
        return bool(self.settings.agnes_api_key)

    async def chat(self, prompt: str) -> str:
        if not self.configured():
            return "AI API key 未配置，请先在 .env.local 填写 AGNES_API_KEY。"
        response = await self.client.chat.completions.create(
            model=self.settings.agnes_text_model,
            messages=[
                {"role": "system", "content": "你是一个友好的 QQ 群管理机器人，回答要简洁、自然。"},
                {"role": "user", "content": prompt},
            ],
        )
        return response.choices[0].message.content or ""

    async def understand_image(self, prompt: str, image_url: str) -> str:
        if not self.configured():
            return "AI API key 未配置，请先在 .env.local 填写 AGNES_API_KEY。"
        data_url = await self._image_data_url(image_url)
        response = await self.client.chat.completions.create(
            model=self.settings.agnes_text_model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt or "请描述并分析这张图片。"},
                        {"type": "image_url", "image_url": {"url": data_url}},
                    ],
                }
            ],
        )
        return response.choices[0].message.content or ""

    async def generate_image(self, prompt: str) -> GeneratedAsset:
        if not self.configured():
            return GeneratedAsset("image", "", {"error": "AGNES_API_KEY missing"})
        response = await self.client.images.generate(
            model=self.settings.agnes_image_model,
            prompt=prompt,
            size="1024x1024",
        )
        item = response.data[0]
        url = getattr(item, "url", "") or ""
        return GeneratedAsset("image", url, response.model_dump())

    async def generate_video(self, prompt: str) -> GeneratedAsset:
        if not self.configured():
            return GeneratedAsset("video", "", {"error": "AGNES_API_KEY missing"})

        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(
                f"{self.settings.agnes_base_url.rstrip('/')}/videos/generations",
                headers={"Authorization": f"Bearer {self.settings.agnes_api_key}"},
                json={"model": self.settings.agnes_video_model, "prompt": prompt},
            )
            response.raise_for_status()
            payload = response.json()
        url = payload.get("url") or payload.get("data", [{}])[0].get("url", "")
        return GeneratedAsset("video", url, payload)

    async def _image_data_url(self, image_url: str) -> str:
        if image_url.startswith("data:"):
            return image_url
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.get(image_url)
            response.raise_for_status()
        content_type = response.headers.get("content-type", "image/jpeg")
        encoded = base64.b64encode(response.content).decode("ascii")
        return f"data:{content_type};base64,{encoded}"
