from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, Http404, JsonResponse
from django.shortcuts import get_object_or_404
from django.core.exceptions import PermissionDenied
from .models import ProposalDocument
from accounts.models import CustomUser

@login_required
def download_proposal_document(request, doc_id):
    """
    Securely serve proposal documents only to authorized users.
    """
    try:
        doc = ProposalDocument.objects.select_related('proposal', 'uploaded_by').get(
            id=doc_id,
            proposal__user=request.user.customuser  # Only allow own user
        )
        print(doc.name)
    except ProposalDocument.DoesNotExist:
        raise Http404("Documento no encontrado o acceso denegado.")

    response = FileResponse(
        doc.file.open(),
        content_type='application/octet-stream'
    )
    response['Content-Disposition'] = f'attachment; filename="{doc.name}"'
    return response