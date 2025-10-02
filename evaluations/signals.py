from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import TemplateItem, EvaluationTemplate


@receiver(post_save, sender=TemplateItem)
def update_template_max_score_on_save(sender, instance, created, **kwargs):
    template = instance.category.template
    template.update_evaluations()


@receiver(post_delete, sender=TemplateItem)
def update_template_max_score_on_delete(sender, instance, **kwargs):
    template = instance.category.template
    template.update_evaluations()