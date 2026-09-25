from .models import Profile
from .permissions import role_for, role_label, sidebar_groups


def role_ui(request):
    if not request.user.is_authenticated:
        return {}
    return {
        'current_role_label': role_label(request.user),
        'sidebar_groups': sidebar_groups(request.user),
        'is_system_admin': (
            request.user.is_superuser
            or request.user.is_staff
            or role_for(request.user) == Profile.Role.SYSTEM_ADMIN
        ),
    }
