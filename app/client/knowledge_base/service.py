import httpx
from retell import Retell
from fastapi import HTTPException, status
from app.config.settings import settings
from app.core.exceptions.base import InternalServerErrorException


client = Retell(api_key=settings.retell_api_key)


class RetellService:
    BASE_URL = "https://api.retellai.com"

    @staticmethod
    async def list_sitemap(website_url):
        """
        📡 Calls Retell AI API to list sitemaps of a given website.
        """
        endpoint = f"{RetellService.BASE_URL}/list-sitemap"
        headers = {
            "Authorization": f"Bearer {settings.retell_api_key}",
            "Content-Type": "application/json",
        }

        # Ensure website_url is a plain string
        payload = {"website_url": str(website_url)}

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(endpoint, json=payload, headers=headers)

            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Retell API error: {response.text}",
                )

            return response.json()

        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"External API request failed: {exc}",
            )



class RetellKnowledgeBaseService:
    """Handles Retell API communication."""

    @staticmethod
    def create_knowledge_base(name: str, texts=None, urls=None, files=None):
        kwargs = {"knowledge_base_name": name}
        if texts:
            kwargs["knowledge_base_texts"] = [t.model_dump() for t in texts]
        if urls:
            kwargs["knowledge_base_urls"] = urls
        if files:
            kwargs["knowledge_base_files"] = files

        try:
            response = client.knowledge_base.create(**kwargs)
            return response
        except Exception as e:
            raise InternalServerErrorException(f"Retell API Error: {str(e)}")
