import httpx
import io
from retell import Retell
from fastapi import HTTPException, status
from app.config.settings import settings
from app.core.exceptions.base import InternalServerErrorException

from app.config.logger import get_logger

logger = get_logger("Knowledge Base service")

client = Retell(api_key=settings.retell_api_key)


class RetellService:
    BASE_URL = "https://api.retellai.com"

    @staticmethod
    async def list_sitemap(website_url):
        """
        Calls Retell AI API to list sitemaps of a given website.
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
    @staticmethod
    async def create_knowledge_base(name, texts=None, urls=None, files=None):
        file_objects = []
        try:
            if files:
                for upload in files:
                    content = await upload.read()
                    file_obj = io.BytesIO(content)
                    file_obj.name = upload.filename
                    file_objects.append(file_obj)

            kwargs = {"knowledge_base_name": name}
            if texts:
                kwargs["knowledge_base_texts"] = [t.model_dump() for t in texts]
            if urls:
                kwargs["knowledge_base_urls"] = urls
            if file_objects:
                kwargs["knowledge_base_files"] = file_objects

            response = client.knowledge_base.create(**kwargs)
            return response

        except Exception as e:
            raise InternalServerErrorException(f"Retell API Error: {str(e)}")

        finally:
            for f in file_objects:
                try:
                    f.close()
                except Exception:
                    pass


    @staticmethod
    async def delete_source_from_retell(source_id: str, knowledge_base_id: str):
        """
        Deletes a specific source from Retell Knowledge Base.
        """
        try:
            response = client.knowledge_base.delete_source(
                source_id=source_id,
                knowledge_base_id=knowledge_base_id,
            )
            return response
        except Exception as e:
            logger.info(f"e __________________ {e}")
            # raise InternalServerErrorException(f"Failed to delete source from Retell: {str(e)}")


    @classmethod
    async def delete_knowledge_base_from_retell(cls, knowledge_base_id: str):
        """
        Delete a knowledge base from Retell platform.
        """
        try:
            response = client.agent.delete(knowledge_base_id)
            return response
        except Exception as e:
            logger.info(f"e __________________ {e}")
            # raise InternalServerErrorException(f"Failed to delete from Retell: {str(e)}")


