from __future__ import annotations

from celery import shared_task

from enterprise_documents.services import DocumentService


@shared_task(name="enterprise_documents.tasks.process_document_task", ignore_result=True)
def process_document_task(document_id: str, actor: str = "celery") -> dict:
    return DocumentService().process_document_by_id(document_id, actor)


@shared_task(name="enterprise_documents.tasks.sync_sii_profile_task", ignore_result=True)
def sync_sii_profile_task(profile_id: int) -> dict:
    return DocumentService().sync_sii_profile(profile_id)


@shared_task(name="enterprise_documents.tasks.sync_enabled_sii_profiles", ignore_result=True)
def sync_enabled_sii_profiles() -> int:
    return DocumentService().sync_enabled_profiles()
