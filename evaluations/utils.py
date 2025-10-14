from django.contrib.contenttypes.models import ContentType
from common.models import Status
from django.core.mail import send_mail
from django.conf import settings
from evaluations.models import Evaluation
from expressions.models import Expression
from proposals.models import Proposal
from accounts.models import CustomUser

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
        print("Not enough evaluations")
        return False  # Not enough evaluations

    if evaluations.filter(is_positive=True).count() < 2:
        print("Not all positive")
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


        # CREATE PROPOSAL AS DRAFT
        draft_status, _ = Status.objects.get_or_create(
            name='Borrador',
            defaults={'description': 'Propuesta creada automáticamente tras aprobación de expresión', 'is_active': True}
        )

        proposal = Proposal.objects.create(
            expression_ptr=expression,
            principal_research_experience="",
            community_description="",
            duration_months=12,
            summary="",
            context_problem_justification="",
            specific_objectives="",
            methodology_analytical_plan_ethics="",
            equity_inclusion="",
            communication_strategy="",
            risk_analysis_mitigation="",
            research_team="",
            status=draft_status,
            created_by=expression.user,
        )

        # AUTO-ASSIGN 2 EVALUATORS TO THE PROPOSAL
        # Get the same evaluators who approved the Expression
        evaluator_ids = evaluations.values_list('evaluator_id', flat=True)
        
        evaluators = CustomUser.objects.filter(id__in=evaluator_ids)

        # Assign each evaluator to the new Proposal
        pending_status, _ = Status.objects.get_or_create(
            name='Pendiente',
            defaults={'description': 'Evaluación pendiente de revisión'}
        )

        content_type_proposal = ContentType.objects.get_for_model(Proposal)

        for evaluator in evaluators:
            Evaluation.objects.get_or_create(
                target_content_type=content_type_proposal,
                target_object_id=proposal.id,
                evaluator=evaluator,
                defaults={
                    'status': pending_status,
                    'template': expression.evaluations.first().template,  # Reuse same template
                    'created_by': expression.user,
                }
            )

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