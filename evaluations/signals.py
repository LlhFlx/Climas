from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db import transaction
from .models import TemplateItem, EvaluationTemplate, TemplateCategory


@receiver(post_save, sender=TemplateItem)
def update_template_max_score_on_save(sender, instance, created, **kwargs):
    template = instance.category.template
    transaction.on_commit(lambda: template.update_evaluations())


@receiver(post_delete, sender=TemplateItem)
def update_template_max_score_on_delete(sender, instance, **kwargs):
    template = instance.category.template
    transaction.on_commit(lambda: template.update_evaluations())

@receiver(post_save, sender=TemplateCategory)
def update_template_on_category_save(sender, instance, **kwargs):
    transaction.on_commit(lambda: instance.template.update_evaluations())

@receiver(post_delete, sender=TemplateCategory)
def update_template_on_category_delete(sender, instance, **kwargs):
    transaction.on_commit(lambda: instance.template.update_evaluations())