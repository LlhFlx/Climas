from django.contrib.contenttypes.models import ContentType
from common.models import Status
from django.core.mail import send_mail
from django.conf import settings
from evaluations.models import Evaluation
from expressions.models import Expression
from proposals.models import Proposal

def approve_if_auto_approved(target_id, target_type):
    """
    If exactly 2 evaluations exist for this target, and both are positive,
    auto-approve the target and mark all evaluations as validated.
    """
    content_type = ContentType.objects.get_for_model(
        Expression if target_type == 'expression' else Proposal
    )

    evaluations = Evaluation.objects.filter(
        target_content_type=content_type,
        target_object_id=target_id
    )

    if evaluations.count() < 2:
        return False  # Not enough evaluations

    if evaluations.filter(is_positive=True).count() < 2:
        return False  # Not all positive

    # All 2 are positive: auto-approve
    evaluations.update(is_validated=True)
    # safe: Use get_or_create for status names
    if target_type == 'expression':
        expression = Expression.objects.get(id=target_id)
        status, created = Status.objects.get_or_create(
            name='Aprobada',
            defaults={
                'description': 'Evaluación autoaprobada por sistema',
                'is_active': True,
                'color': 'green'
            }
        )
        expression.status = status
        expression.save()
        return True
    else:
        proposal = Proposal.objects.get(id=target_id)
        status, created = Status.objects.get_or_create(
            name='Aprobada para Financiamiento',
            defaults={
                'description': 'Propuesta autoaprobada para financiamiento por sistema',
                'is_active': True,
                'color': 'blue'
            }
        )
        proposal.status = status
        proposal.save()
        return True

    return False