from django import forms
from django.forms import modelform_factory

from . import models


class StyledModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            css_class = 'form-control'
            if isinstance(field.widget, forms.CheckboxInput):
                css_class = 'form-check-input'
            elif isinstance(field.widget, forms.Select):
                css_class = 'form-select'
            field.widget.attrs.setdefault('class', css_class)


class ProjectForm(StyledModelForm):
    class Meta:
        model = models.Project
        fields = '__all__'
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'original_completion_date': forms.DateInput(attrs={'type': 'date'}),
            'revised_completion_date': forms.DateInput(attrs={'type': 'date'}),
        }


class DailyReportForm(StyledModelForm):
    class Meta:
        model = models.DailyReport
        fields = '__all__'
        widgets = {
            'report_date': forms.DateInput(attrs={'type': 'date'}),
            'work_completed': forms.Textarea(attrs={'rows': 4}),
            'problems': forms.Textarea(attrs={'rows': 3}),
            'safety_incidents': forms.Textarea(attrs={'rows': 3}),
        }


FORM_MODELS = {
    'companies': models.Company,
    'departments': models.Department,
    'partners': models.BusinessPartner,
    'projects': models.Project,
    'team': models.ProjectTeamMember,
    'contracts': models.Contract,
    'boq-sections': models.BOQSection,
    'boq-items': models.BOQItem,
    'budgets': models.BudgetItem,
    'materials': models.Material,
    'stock': models.StockMovement,
    'purchase-requests': models.PurchaseRequest,
    'purchase-orders': models.PurchaseOrder,
    'activities': models.Activity,
    'daily-reports': models.DailyReport,
    'rfis': models.RFI,
    'variations': models.Variation,
    'eot': models.EOTApplication,
    'payments': models.PaymentCertificate,
    'invoices': models.Invoice,
    'documents': models.Document,
    'risks': models.Risk,
    'safety': models.SafetyIncident,
    'defects': models.Defect,
    'tasks': models.ProjectTask,
    'approvals': models.ApprovalRequest,
}


FORM_CLASSES = {
    'projects': ProjectForm,
    'daily-reports': DailyReportForm,
}


def get_entity_form(entity):
    if entity in FORM_CLASSES:
        return FORM_CLASSES[entity]
    model = FORM_MODELS[entity]
    return modelform_factory(model, form=StyledModelForm, fields='__all__')
