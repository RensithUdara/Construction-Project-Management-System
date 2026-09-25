from .models import Profile


ALL_MODULES = {
    'companies',
    'departments',
    'partners',
    'projects',
    'team',
    'contracts',
    'boq-sections',
    'boq-items',
    'budgets',
    'materials',
    'stock',
    'purchase-requests',
    'purchase-orders',
    'activities',
    'daily-reports',
    'rfis',
    'variations',
    'eot',
    'payments',
    'invoices',
    'documents',
    'risks',
    'safety',
    'defects',
    'tasks',
    'approvals',
}


ROLE_RULES = {
    Profile.Role.SYSTEM_ADMIN: {
        'view': ALL_MODULES,
        'change': ALL_MODULES,
        'export': ALL_MODULES,
    },
    Profile.Role.COMPANY_ADMIN: {
        'view': ALL_MODULES,
        'change': ALL_MODULES - {'payments', 'invoices'},
        'export': ALL_MODULES,
    },
    Profile.Role.PROJECT_MANAGER: {
        'view': ALL_MODULES - {'companies', 'departments'},
        'change': {'projects', 'team', 'activities', 'daily-reports', 'risks', 'safety', 'defects', 'tasks', 'documents', 'rfis'},
        'export': {'projects', 'activities', 'daily-reports', 'risks', 'safety', 'defects', 'tasks', 'documents', 'rfis'},
    },
    Profile.Role.QUANTITY_SURVEYOR: {
        'view': {'projects', 'contracts', 'boq-sections', 'boq-items', 'budgets', 'variations', 'eot', 'payments', 'invoices', 'documents', 'tasks'},
        'change': {'boq-sections', 'boq-items', 'budgets', 'variations', 'eot', 'payments', 'documents', 'tasks'},
        'export': {'projects', 'contracts', 'boq-sections', 'boq-items', 'budgets', 'variations', 'eot', 'payments', 'invoices'},
    },
    Profile.Role.SITE_ENGINEER: {
        'view': {'projects', 'team', 'materials', 'stock', 'activities', 'daily-reports', 'documents', 'rfis', 'risks', 'safety', 'defects', 'tasks'},
        'change': {'stock', 'activities', 'daily-reports', 'documents', 'rfis', 'risks', 'safety', 'defects', 'tasks'},
        'export': {'projects', 'materials', 'stock', 'activities', 'daily-reports', 'rfis', 'risks', 'safety', 'defects', 'tasks'},
    },
    Profile.Role.PROCUREMENT: {
        'view': {'projects', 'partners', 'materials', 'stock', 'purchase-requests', 'purchase-orders', 'documents', 'tasks', 'invoices'},
        'change': {'partners', 'materials', 'stock', 'purchase-requests', 'purchase-orders', 'documents', 'tasks'},
        'export': {'partners', 'materials', 'stock', 'purchase-requests', 'purchase-orders', 'invoices'},
    },
    Profile.Role.FINANCE: {
        'view': {'projects', 'contracts', 'budgets', 'purchase-orders', 'payments', 'invoices', 'documents', 'tasks'},
        'change': {'budgets', 'payments', 'invoices', 'documents', 'tasks'},
        'export': {'projects', 'contracts', 'budgets', 'purchase-orders', 'payments', 'invoices'},
    },
    Profile.Role.CONSULTANT: {
        'view': {'projects', 'activities', 'documents', 'rfis', 'variations', 'eot', 'payments', 'risks', 'safety', 'defects', 'tasks', 'approvals'},
        'change': {'documents', 'rfis', 'variations', 'eot', 'risks', 'defects', 'tasks', 'approvals'},
        'export': {'projects', 'documents', 'rfis', 'variations', 'eot', 'payments', 'risks', 'safety', 'defects'},
    },
    Profile.Role.CONTRACTOR: {
        'view': {'projects', 'activities', 'daily-reports', 'documents', 'rfis', 'variations', 'eot', 'payments', 'defects', 'tasks'},
        'change': {'daily-reports', 'documents', 'rfis', 'variations', 'eot', 'payments', 'defects', 'tasks'},
        'export': {'projects', 'activities', 'daily-reports', 'documents', 'rfis', 'variations', 'eot', 'payments', 'defects'},
    },
}


SIDEBAR_GROUPS = [
    ('Project Control', [
        ('projects', 'Projects'),
        ('activities', 'Schedule'),
        ('daily-reports', 'Daily Reports'),
        ('tasks', 'Tasks'),
    ]),
    ('Commercial', [
        ('contracts', 'Contracts'),
        ('boq-items', 'BOQ'),
        ('budgets', 'Budgets'),
        ('variations', 'Variations'),
        ('payments', 'Payments'),
        ('invoices', 'Invoices'),
    ]),
    ('Operations', [
        ('purchase-requests', 'Procurement'),
        ('materials', 'Materials'),
        ('documents', 'Documents'),
        ('rfis', 'RFIs'),
        ('risks', 'Risk & Safety'),
        ('defects', 'Defects'),
    ]),
    ('Organization', [
        ('companies', 'Companies'),
        ('departments', 'Departments'),
        ('partners', 'Business Partners'),
        ('team', 'Project Team'),
    ]),
]


def role_for(user):
    if not user.is_authenticated:
        return None
    if user.is_superuser:
        return Profile.Role.SYSTEM_ADMIN
    profile = getattr(user, 'profile', None)
    return profile.role if profile else None


def role_label(user):
    profile = getattr(user, 'profile', None)
    if profile:
        return profile.get_role_display()
    return 'System Administrator' if getattr(user, 'is_superuser', False) else 'User'


def _allowed(user, action):
    role = role_for(user)
    if not role:
        return set()
    return ROLE_RULES.get(role, {}).get(action, set())


def can_view(user, entity):
    return entity in _allowed(user, 'view')


def can_change(user, entity):
    return entity in _allowed(user, 'change')


def can_export(user, entity):
    return entity in _allowed(user, 'export')


def sidebar_groups(user):
    groups = []
    for title, links in SIDEBAR_GROUPS:
        visible_links = [
            {'entity': entity, 'label': label}
            for entity, label in links
            if can_view(user, entity)
        ]
        if visible_links:
            groups.append({'title': title, 'links': visible_links})
    return groups
