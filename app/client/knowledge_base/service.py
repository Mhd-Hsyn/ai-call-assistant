from retell import Retell
from app.config.settings import settings
from app.core.exceptions.base import InternalServerErrorException

client = Retell(api_key=settings.retell_api_key)


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
