from .permissions import role_label, sidebar_groups


def role_ui(request):
    if not request.user.is_authenticated:
        return {}
    return {
        'current_role_label': role_label(request.user),
        'sidebar_groups': sidebar_groups(request.user),
    }
