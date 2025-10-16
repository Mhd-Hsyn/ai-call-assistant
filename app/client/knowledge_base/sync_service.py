import json
from retell import Retell
from beanie.operators import And
from app.config.settings import settings
from app.client.models import KnowledgeBaseModel, KnowledgeBaseSourceModel
from app.core.constants.choices import KnowledgeBaseSourceTypeChoices, KnowledgeBaseStatusChoices
from app.config.logger import get_logger
from app.auth.models import UserModel

logger = get_logger("Retell Sync KnowledgeBase Service")


class RetellSyncService:
    client = Retell(api_key=settings.retell_api_key)

    @staticmethod
    async def sync_in_progress_knowledge_bases():
        """
        Sync all IN_PROGRESS knowledge bases globally.
        """
        return await RetellSyncService._sync_kbs(
            filters={KnowledgeBaseModel.status: KnowledgeBaseStatusChoices.IN_PROGRESS},
            log_prefix="(GLOBAL)",
        )

    @staticmethod
    async def sync_user_knowledge_bases(user: UserModel):
        """
        Sync all IN_PROGRESS knowledge bases for a specific user.
        """
        return await RetellSyncService._sync_kbs(
            filters={
                KnowledgeBaseModel.user.id: user.id,
                KnowledgeBaseModel.status: KnowledgeBaseStatusChoices.IN_PROGRESS,
            },
            log_prefix=f"(USER: {user.email})",
        )

    @staticmethod
    async def _sync_kbs(filters: dict, log_prefix: str = ""):
        """
        Core sync function used for both global & user-specific syncs.
        """
        query = And(*[k == v for k, v in filters.items()])
        kbs = await KnowledgeBaseModel.find(query).to_list()

        if not kbs:
            return {"message": "No IN_PROGRESS knowledge bases found"}

        synced_kbs = []

        for kb in kbs:
            try:
                logger.info(f"{log_prefix} Syncing KB: {kb.knowledge_base_id}")

                kb_data = RetellSyncService.client.knowledge_base.retrieve(kb.knowledge_base_id)
                json_dict = json.loads(kb_data.model_dump_json())

                # Update KB status if changed
                if json_dict.get("status") and json_dict["status"] != kb.status:
                    kb.status = json_dict["status"]
                    await kb.save()

                # Sync sources
                await RetellSyncService._sync_sources(kb, json_dict.get("knowledge_base_sources", []))

                synced_kbs.append(kb.knowledge_base_id)

            except Exception as e:
                logger.exception(f"{log_prefix} Failed to sync {kb.knowledge_base_id}: {str(e)}")

        return {
            "message": f"Synced {len(synced_kbs)} knowledge bases",
            "synced_ids": synced_kbs,
        }


    @staticmethod
    async def _sync_sources(kb: KnowledgeBaseModel, sources: list):
        """
        Add missing sources to DB (skip if already exists).
        """
        for src in sources:
            source_id = src.get("source_id")
            if not source_id:
                continue

            existing = await KnowledgeBaseSourceModel.find_one(
                KnowledgeBaseSourceModel.source_id == source_id
            )
            if existing:
                continue

            # Determine source type
            src_type = src.get("type")
            if src_type not in KnowledgeBaseSourceTypeChoices.__members__.values():
                src_type = KnowledgeBaseSourceTypeChoices.URL

            new_source = KnowledgeBaseSourceModel(
                knowledge_base=kb,
                source_id=source_id,
                type=src_type,
                title=src.get("title") or src.get("filename"),
                url=src.get("url") or src.get("file_url") or src.get("content_url"),
            )
            await new_source.insert()

        logger.info(f"Synced sources for KB: {kb.knowledge_base_id}")

