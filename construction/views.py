import csv

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.db.models import Count, Q, Sum
from django.utils import timezone
from django.shortcuts import get_object_or_404, redirect, render
from rest_framework import permissions, viewsets
from rest_framework.routers import DefaultRouter

from . import models
from .forms import FORM_MODELS, get_entity_form
from .permissions import can_change, can_export, can_view
from .serializers import serializer_for


ENTITY_CONFIG = {
    'companies': {'title': 'Companies', 'fields': ['name', 'email', 'phone']},
    'departments': {'title': 'Departments', 'fields': ['company', 'name']},
    'partners': {'title': 'Business Partners', 'fields': ['partner_type', 'name', 'contact_person', 'phone']},
    'projects': {'title': 'Projects', 'fields': ['code', 'name', 'company', 'status', 'contract_value']},
    'team': {'title': 'Project Team', 'fields': ['project', 'user', 'project_role', 'active']},
    'contracts': {'title': 'Contracts', 'fields': ['project', 'contract_type', 'framework', 'contract_value']},
    'boq-sections': {'title': 'BOQ Sections', 'fields': ['project', 'code', 'title']},
    'boq-items': {'title': 'BOQ Items', 'fields': ['section', 'item_number', 'unit', 'quantity', 'rate', 'amount']},
    'budgets': {'title': 'Budgets', 'fields': ['project', 'category', 'current_budget', 'actual_cost', 'variance']},
    'materials': {'title': 'Materials', 'fields': ['name', 'category', 'unit', 'current_stock', 'minimum_stock']},
    'stock': {'title': 'Stock Movements', 'fields': ['material', 'project', 'movement_type', 'quantity']},
    'purchase-requests': {'title': 'Purchase Requests', 'fields': ['request_number', 'project', 'material', 'quantity', 'status']},
    'purchase-orders': {'title': 'Purchase Orders', 'fields': ['po_number', 'project', 'supplier', 'total_amount', 'status']},
    'activities': {'title': 'Schedule Activities', 'fields': ['code', 'project', 'name', 'status', 'progress']},
    'daily-reports': {'title': 'Daily Reports', 'fields': ['project', 'report_date', 'weather', 'workers_count']},
    'rfis': {'title': 'RFIs', 'fields': ['rfi_number', 'project', 'subject', 'priority', 'status']},
    'variations': {'title': 'Variations', 'fields': ['variation_number', 'project', 'status', 'additional_cost']},
    'eot': {'title': 'EOT Applications', 'fields': ['eot_number', 'project', 'delay_event', 'delay_duration', 'status']},
    'payments': {'title': 'Payment Certificates', 'fields': ['certificate_number', 'project', 'gross_amount', 'net_amount', 'status']},
    'invoices': {'title': 'Invoices', 'fields': ['invoice_number', 'project', 'supplier', 'total', 'status']},
    'documents': {'title': 'Documents', 'fields': ['project', 'title', 'category', 'version', 'status']},
    'risks': {'title': 'Risks', 'fields': ['project', 'title', 'probability', 'impact', 'risk_score', 'status']},
    'safety': {'title': 'Safety Incidents', 'fields': ['project', 'incident_date', 'title', 'severity', 'closed']},
    'defects': {'title': 'Defects', 'fields': ['defect_number', 'project', 'location', 'priority', 'status']},
    'tasks': {'title': 'Tasks', 'fields': ['project', 'title', 'assignee', 'priority', 'status']},
    'approvals': {'title': 'Approvals', 'fields': ['project', 'title', 'approver', 'status']},
}


def _entity_or_404(entity):
    if entity not in FORM_MODELS:
        raise KeyError(entity)
    return FORM_MODELS[entity], ENTITY_CONFIG[entity]


def _display_value(obj, field_name):
    value = getattr(obj, field_name)
    if callable(value):
        value = value()
    return value


def _text_search_fields(model):
    return [
        field.name
        for field in model._meta.fields
        if field.get_internal_type() in {'CharField', 'TextField', 'EmailField'}
    ]


def _query_text_fields(model, query):
    search_query = Q()
    for field in _text_search_fields(model):
        search_query |= Q(**{f'{field}__icontains': query})
    return search_query


def _export_csv(qs, config):
    response = HttpResponse(content_type='text/csv')
    filename = config['title'].lower().replace(' ', '-')
    response['Content-Disposition'] = f'attachment; filename="{filename}.csv"'
    writer = csv.writer(response)
    writer.writerow([field.replace('_', ' ').title() for field in config['fields']])
    for obj in qs:
        writer.writerow([_display_value(obj, field) for field in config['fields']])
    return response


@login_required
def dashboard(request):
    projects = models.Project.objects.select_related('company').all()
    today = timezone.localdate()
    active_statuses = [
        models.Project.Status.MOBILIZATION,
        models.Project.Status.CONSTRUCTION,
        models.Project.Status.PRACTICAL_COMPLETION,
    ]
    project_status_counts = dict(projects.values_list('status').annotate(total=Count('id')))
    budget_rows = list(
        models.BudgetItem.objects.values('category')
        .annotate(budget=Sum('current_budget'), actual=Sum('actual_cost'), committed=Sum('committed_cost'))
        .order_by('category')
    )
    project_progress = [
        {'label': project.code, 'value': float(project.progress_percent)}
        for project in projects[:8]
    ]
    workflow_counts = {
        'RFIs': models.RFI.objects.exclude(status=models.RFI.Status.CLOSED).count(),
        'Variations': models.Variation.objects.exclude(status__in=[models.Variation.Status.APPROVED, models.Variation.Status.REJECTED]).count(),
        'EOT': models.EOTApplication.objects.exclude(status__in=[models.EOTApplication.Status.APPROVED, models.EOTApplication.Status.REJECTED]).count(),
        'Approvals': models.ApprovalRequest.objects.filter(status=models.ApprovalRequest.Status.PENDING).count(),
        'Defects': models.Defect.objects.exclude(status=models.Defect.Status.CLOSED).count(),
    }
    overdue_tasks = models.ProjectTask.objects.filter(due_date__lt=today).exclude(status=models.ProjectTask.Status.COMPLETED)
    overdue_rfis = models.RFI.objects.filter(due_date__lt=today).exclude(status=models.RFI.Status.CLOSED)
    context = {
        'total_projects': projects.count(),
        'active_projects': projects.filter(status__in=active_statuses).count(),
        'completed_projects': projects.filter(status=models.Project.Status.FINAL_COMPLETION).count(),
        'contract_value': projects.aggregate(total=Sum('contract_value'))['total'] or 0,
        'actual_cost': models.BudgetItem.objects.aggregate(total=Sum('actual_cost'))['total'] or 0,
        'open_rfis': models.RFI.objects.exclude(status=models.RFI.Status.CLOSED).count(),
        'pending_approvals': models.ApprovalRequest.objects.filter(status=models.ApprovalRequest.Status.PENDING).count(),
        'open_defects': models.Defect.objects.exclude(status=models.Defect.Status.CLOSED).count(),
        'safety_open': models.SafetyIncident.objects.filter(closed=False).count(),
        'recent_projects': projects[:6],
        'risk_counts': models.Risk.objects.values('status').annotate(total=Count('id')),
        'module_links': ENTITY_CONFIG,
        'visible_module_links': {key: value for key, value in ENTITY_CONFIG.items() if can_view(request.user, key)},
        'can_create_projects': can_change(request.user, 'projects'),
        'can_create_daily_reports': can_change(request.user, 'daily-reports'),
        'can_create_rfis': can_change(request.user, 'rfis'),
        'recent_audits': models.AuditLog.objects.select_related('user')[:8],
        'overdue_tasks': overdue_tasks.select_related('project', 'assignee')[:6],
        'overdue_rfis': overdue_rfis.select_related('project')[:6],
        'dashboard_charts': {
            'projectStatus': {
                'labels': [label for _value, label in models.Project.Status.choices],
                'values': [project_status_counts.get(value, 0) for value, _label in models.Project.Status.choices],
            },
            'budget': {
                'labels': [models.BudgetItem.Category(row['category']).label for row in budget_rows],
                'budget': [float(row['budget'] or 0) for row in budget_rows],
                'actual': [float(row['actual'] or 0) for row in budget_rows],
                'committed': [float(row['committed'] or 0) for row in budget_rows],
            },
            'projectProgress': project_progress,
            'workflow': {
                'labels': list(workflow_counts.keys()),
                'values': list(workflow_counts.values()),
            },
        },
    }
    return render(request, 'construction/dashboard.html', context)


@login_required
def entity_list(request, entity):
    model, config = _entity_or_404(entity)
    if not can_view(request.user, entity):
        raise PermissionDenied
    qs = model.objects.all()
    query = request.GET.get('q', '').strip()
    if query:
        qs = qs.filter(_query_text_fields(model, query))
    if not qs.query.order_by and not model._meta.ordering:
        qs = qs.order_by('-pk')
    if request.GET.get('export') == 'csv':
        if not can_export(request.user, entity):
            raise PermissionDenied
        return _export_csv(qs, config)
    paginator = Paginator(qs, 20)
    page = paginator.get_page(request.GET.get('page'))
    rows = [
        {'object': obj, 'values': [(field, _display_value(obj, field)) for field in config['fields']]}
        for obj in page.object_list
    ]
    return render(request, 'construction/entity_list.html', {
        'entity': entity,
        'config': config,
        'page': page,
        'rows': rows,
        'query': query,
        'can_create': can_change(request.user, entity),
        'can_edit': can_change(request.user, entity),
        'can_export': can_export(request.user, entity),
    })


@login_required
def entity_create(request, entity):
    _model, config = _entity_or_404(entity)
    if not can_change(request.user, entity):
        raise PermissionDenied
    form_class = get_entity_form(entity)
    form = form_class(request.POST or None, request.FILES or None)
    if form.is_valid():
        obj = form.save()
        messages.success(request, f'{config["title"][:-1] if config["title"].endswith("s") else config["title"]} saved.')
        if isinstance(obj, models.Project):
            return redirect(obj)
        return redirect('entity_list', entity=entity)
    return render(request, 'construction/entity_form.html', {'form': form, 'config': config, 'entity': entity, 'mode': 'Create'})


@login_required
def entity_update(request, entity, pk):
    model, config = _entity_or_404(entity)
    if not can_change(request.user, entity):
        raise PermissionDenied
    obj = get_object_or_404(model, pk=pk)
    form_class = get_entity_form(entity)
    form = form_class(request.POST or None, request.FILES or None, instance=obj)
    if form.is_valid():
        obj = form.save()
        messages.success(request, 'Changes saved.')
        if isinstance(obj, models.Project):
            return redirect(obj)
        return redirect('entity_list', entity=entity)
    return render(request, 'construction/entity_form.html', {'form': form, 'config': config, 'entity': entity, 'mode': 'Edit', 'object': obj})


@login_required
def project_detail(request, pk):
    if not can_view(request.user, 'projects'):
        raise PermissionDenied
    project = get_object_or_404(models.Project.objects.select_related('company', 'client', 'consultant', 'contractor'), pk=pk)
    context = {
        'project': project,
        'budget_items': project.budget_items.all(),
        'activities': project.activities.all()[:12],
        'rfis': project.rfis.all()[:8],
        'variations': project.variations.all()[:8],
        'documents': project.documents.all()[:8],
        'tasks': project.tasks.all()[:8],
        'risks': project.risks.all()[:8],
        'defects': project.defects.all()[:8],
        'can_edit_project': can_change(request.user, 'projects'),
    }
    return render(request, 'construction/project_detail.html', context)


class BaseModelViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = '__all__'
    search_fields = ['id']
    ordering_fields = '__all__'


router = DefaultRouter()

for entity, model in FORM_MODELS.items():
    serializer_class = serializer_for(model)
    viewset = type(
        f'{model.__name__}ViewSet',
        (BaseModelViewSet,),
        {
            'queryset': model.objects.all(),
            'serializer_class': serializer_class,
        },
    )
    router.register(entity, viewset, basename=entity)
