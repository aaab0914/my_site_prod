import logging

from celery import shared_task
from django.apps import apps
from django.core.exceptions import ObjectDoesNotExist
from django_elasticsearch_dsl.registries import registry
from django_elasticsearch_dsl.signals import CelerySignalProcessor, RealTimeSignalProcessor

logger = logging.getLogger(__name__)


@shared_task(ignore_result=True)
def safe_registry_update_task(pk, app_label, model_name):
    try:
        model = apps.get_model(app_label, model_name)
    except LookupError:
        logger.warning("Elasticsearch update skipped for missing model %s.%s", app_label, model_name)
        return

    try:
        instance = model._default_manager.get(pk=pk)
    except ObjectDoesNotExist:
        logger.info("Elasticsearch update skipped for missing %s.%s pk=%s", app_label, model_name, pk)
        return

    try:
        registry.update(instance)
    except Exception:
        logger.exception("Elasticsearch registry.update failed for %s.%s pk=%s", app_label, model_name, pk)


@shared_task(ignore_result=True)
def safe_registry_update_related_task(pk, app_label, model_name):
    try:
        model = apps.get_model(app_label, model_name)
    except LookupError:
        logger.warning("Elasticsearch related update skipped for missing model %s.%s", app_label, model_name)
        return

    try:
        instance = model._default_manager.get(pk=pk)
    except ObjectDoesNotExist:
        logger.info("Elasticsearch related update skipped for missing %s.%s pk=%s", app_label, model_name, pk)
        return

    try:
        registry.update_related(instance)
    except Exception:
        logger.exception("Elasticsearch registry.update_related failed for %s.%s pk=%s", app_label, model_name, pk)


class ResilientRealTimeSignalProcessor(RealTimeSignalProcessor):
    def handle_save(self, sender, instance, **kwargs):
        try:
            super().handle_save(sender, instance, **kwargs)
        except Exception:
            logger.exception("Elasticsearch autosync failed on save for %s(pk=%s)", sender.__name__, getattr(instance, "pk", None))

    def handle_delete(self, sender, instance, **kwargs):
        try:
            super().handle_delete(sender, instance, **kwargs)
        except Exception:
            logger.exception("Elasticsearch autosync failed on delete for %s(pk=%s)", sender.__name__, getattr(instance, "pk", None))

    def handle_m2m_changed(self, sender, instance, action, **kwargs):
        try:
            super().handle_m2m_changed(sender, instance, action, **kwargs)
        except Exception:
            logger.exception(
                "Elasticsearch autosync failed on m2m change for %s(pk=%s), action=%s",
                instance.__class__.__name__,
                getattr(instance, "pk", None),
                action,
            )

    def handle_pre_delete(self, sender, instance, **kwargs):
        try:
            super().handle_pre_delete(sender, instance, **kwargs)
        except Exception:
            logger.exception("Elasticsearch autosync failed on pre-delete for %s(pk=%s)", sender.__name__, getattr(instance, "pk", None))


class ResilientCelerySignalProcessor(CelerySignalProcessor):
    def handle_save(self, sender, instance, **kwargs):
        try:
            safe_registry_update_task.delay(instance.pk, instance._meta.app_label, instance.__class__.__name__)
            safe_registry_update_related_task.delay(instance.pk, instance._meta.app_label, instance.__class__.__name__)
        except Exception:
            logger.exception("Elasticsearch autosync enqueue failed on save for %s(pk=%s)", sender.__name__, getattr(instance, "pk", None))

    def handle_delete(self, sender, instance, **kwargs):
        try:
            super().handle_delete(sender, instance, **kwargs)
        except Exception:
            logger.exception("Elasticsearch autosync enqueue failed on delete for %s(pk=%s)", sender.__name__, getattr(instance, "pk", None))

    def handle_pre_delete(self, sender, instance, **kwargs):
        try:
            super().handle_pre_delete(sender, instance, **kwargs)
        except Exception:
            logger.exception("Elasticsearch autosync enqueue failed on pre-delete for %s(pk=%s)", sender.__name__, getattr(instance, "pk", None))
