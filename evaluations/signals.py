from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db import transaction
from .models import (
    TemplateItem, 
    TemplateSubcategory, 
    TemplateCategory, 
    EvaluationTemplate, 
    TemplateItemOption
)

# Re-calculate whenever any part of the hierarchy changes
@receiver([post_save, post_delete], sender=TemplateItem)
@receiver([post_save, post_delete], sender=TemplateSubcategory)
@receiver([post_save, post_delete], sender=TemplateCategory)
def trigger_template_update(sender, instance, **kwargs):
    if sender == TemplateItem:
        template = instance.subcategory.category.template
    elif sender == TemplateSubcategory:
        template = instance.category.template
    elif sender == TemplateCategory:
        template = instance.template
    else:
        return
    transaction.on_commit(lambda: template.update_evaluations())

@receiver([post_save, post_delete], sender=TemplateItemOption)
def update_item_max_score(sender, instance, **kwargs):
    """Update the parent TemplateItem's max_score when an option changes."""
    item = instance.item
    item.sync_max_score()
    computed_max = item.calculate_max_score_from_options()
    if computed_max is not None:
        # Only update if different to avoid unnecessary saves
        if item.max_score != computed_max:
            item.max_score = computed_max
            item.save(update_fields=['max_score'])

# @receiver(post_save, sender=TemplateItem)
# def update_template_max_score_on_save(sender, instance, created, **kwargs):
#     template = instance.category.template
#     transaction.on_commit(lambda: template.update_evaluations())


# @receiver(post_delete, sender=TemplateItem)
# def update_template_max_score_on_delete(sender, instance, **kwargs):
#     template = instance.category.template
#     transaction.on_commit(lambda: template.update_evaluations())

# @receiver(post_save, sender=TemplateCategory)
# def update_template_on_category_save(sender, instance, **kwargs):
#     transaction.on_commit(lambda: instance.template.update_evaluations())

# @receiver(post_delete, sender=TemplateCategory)
# def update_template_on_category_delete(sender, instance, **kwargs):
#     transaction.on_commit(lambda: instance.template.update_evaluations())