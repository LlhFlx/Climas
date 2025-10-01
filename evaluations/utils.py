from django.contrib.contenttypes.models import ContentType
from common.models import Status
from django.core.mail import send_mail
from django.conf import settings
from evaluations.models import Evaluation
from expressions.models import Expression
from proposals.models import Proposal

def approve_if_auto_approved(target_id, target_type):
    """
    If exactly 3 evaluations exist for this target, and all are positive,
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

    # All 3 are positive: auto-approve
    evaluations.update(is_validated=True)

    if target_type == 'expression':
        expression = Expression.objects.get(id=target_id)
        expression.status = Status.objects.get(name='Aprobada')
        expression.save()
        return True
    else:
        proposal = Proposal.objects.get(id=target_id)
        proposal.status = Status.objects.get(name='Aprobada para Financiamiento')
        proposal.save()
        return True

    return False