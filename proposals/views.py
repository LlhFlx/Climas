from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, Http404, JsonResponse
from django.shortcuts import get_object_or_404
from django.core.exceptions import PermissionDenied
from .models import ProposalDocument
from accounts.models import CustomUser
from .models import Proposal
from institutions.models import Institution

@login_required
def download_proposal_document(request, doc_id):
    """
    Securely serve proposal documents only to authorized users.
    """
    print("Got id", doc_id)
    try:
        doc = ProposalDocument.objects.select_related('proposal', 'uploaded_by').get(
            id=doc_id,
            proposal__user=request.user.customuser  # Only allow own user
        )
        print(doc.name)
    except ProposalDocument.DoesNotExist:
        raise Http404("Documento no encontrado o acceso denegado.")

    # Guess file type (e.g., application/pdf, image/png)
    import mimetypes
    mime_type, _ = mimetypes.guess_type(doc.file.name)
    if not mime_type:
        mime_type = 'application/octet-stream'

    # Open the file
    file_handle = doc.file.open()

    # Decide between inline or attachment
    response = FileResponse(file_handle, content_type=mime_type)
    print(mime_type)
    if mime_type in ['application/pdf', 'image/png', 'image/jpeg', 'image/jpg']:
        # Browser can render these → show inline
        response['Content-Disposition'] = f'inline; filename="{doc.name}"'
    else:
        # Force download for other file types
        response['Content-Disposition'] = f'attachment; filename="{doc.name}"'

    return response

@login_required
def add_institution_to_proposal(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido.'})

    if not hasattr(request.user, 'customuser') or request.user.customuser.role.name != 'Researcher':
        return JsonResponse({'success': False, 'error': 'Acceso denegado.'})

    institution_id = request.POST.get('institution_id')
    proposal_id = request.POST.get('proposal_id')

    if not institution_id or not proposal_id:
        return JsonResponse({'success': False, 'error': 'Institución o propuesta no especificadas.'})

    try:
        institution = Institution.objects.get(id=institution_id)
        proposal = Proposal.objects.get(pk=proposal_id)

        # Optional: Validate institution is active
        if not institution.is_active:
            return JsonResponse({'success': False, 'error': 'Institución no activa.'})

        # Add institution to proposal
        proposal.partner_institutions.add(institution)

        return JsonResponse({
            'success': True,
            'institution_id': institution.id,
            'institution_name': institution.name,
        })

    except Institution.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Institución no encontrada.'})
    except Proposal.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Propuesta no encontrada.'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': 'Error interno del servidor.'})
    

@login_required
def remove_institution_from_proposal(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido.'})

    if not hasattr(request.user, 'customuser') or request.user.customuser.role.name != 'Researcher':
        return JsonResponse({'success': False, 'error': 'Acceso denegado.'})

    institution_id = request.POST.get('institution_id')
    proposal_id = request.POST.get('proposal_id')

    if not institution_id or not proposal_id:
        return JsonResponse({'success': False, 'error': 'Institución o propuesta no especificadas.'})

    try:
        institution = Institution.objects.get(id=institution_id)
        proposal = Proposal.objects.get(pk=proposal_id)

        # Remove institution from proposal
        proposal.partner_institutions.remove(institution)

        return JsonResponse({
            'success': True,
            'institution_id': institution.id,
        })

    except Institution.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Institución no encontrada.'})
    except Proposal.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Propuesta no encontrada.'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': 'Error interno del servidor.'})