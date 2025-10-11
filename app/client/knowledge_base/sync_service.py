import json
from retell import Retell
from app.config.settings import settings
from app.client.models import KnowledgeBaseModel, KnowledgeBaseSourceModel
from app.core.constants.choices import KnowledgeBaseSourceTypeChoices, KnowledgeBaseStatusChoices
from app.config.logger_config import get_logger

logger = get_logger("Retell Sync KnowledgeBase Service")


client = Retell(api_key=settings.retell_api_key)


class RetellSyncService:
    client = Retell(api_key=settings.retell_api_key)

    @staticmethod
    async def sync_in_progress_knowledge_bases():
        """
        🔁 Fetch all IN_PROGRESS knowledge bases and sync with Retell API.
        """
        # Step 1: Get all KBs in progress
        in_progress_kbs = await KnowledgeBaseModel.find(
            KnowledgeBaseModel.status == KnowledgeBaseStatusChoices.IN_PROGRESS
        ).to_list()

        if not in_progress_kbs:
            return {"message": "No IN_PROGRESS knowledge bases found"}

        synced_kbs = []

        for kb in in_progress_kbs:
            try:
                logger.info(f"🔄 Syncing KB: {kb.knowledge_base_id}")

                # Step 2: Call Retell API
                kb_data = RetellSyncService.client.knowledge_base.retrieve(kb.knowledge_base_id)
                json_dict = json.loads(kb_data.model_dump_json())

                # Step 3: Update KB status if changed
                if json_dict.get("status") and json_dict["status"] != kb.status:
                    kb.status = json_dict["status"]
                    await kb.save()

                # Step 4: Sync sources
                await RetellSyncService._sync_sources(kb, json_dict.get("knowledge_base_sources", []))

                synced_kbs.append(kb.knowledge_base_id)

            except Exception as e:
                logger.exception(f"❌ Failed to sync {kb.knowledge_base_id}: {str(e)}")

        return {
            "message": f"Synced {len(synced_kbs)} knowledge bases",
            "synced_ids": synced_kbs,
        }

    @staticmethod
    async def _sync_sources(kb: KnowledgeBaseModel, sources: list):
        """
        🔗 Add missing sources to DB (skip if already exists).
        """
        for src in sources:
            source_id = src.get("source_id")
            if not source_id:
                continue

            existing = await KnowledgeBaseSourceModel.find_one(
                KnowledgeBaseSourceModel.source_id == source_id
            )

            if existing:
                continue  # ✅ already exists

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

        logger.info(f"✅ Synced sources for KB: {kb.knowledge_base_id}")
