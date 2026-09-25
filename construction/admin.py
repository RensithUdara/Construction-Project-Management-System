from django.contrib import admin

from . import models


@admin.register(models.Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'registration_number', 'email', 'phone')
    search_fields = ('name', 'registration_number', 'email')


@admin.register(models.Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'company', 'role', 'department', 'designation')
    list_filter = ('role', 'company', 'department')
    search_fields = ('user__username', 'user__first_name', 'user__last_name')


@admin.register(models.Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'company', 'project_type', 'status', 'contract_value')
    list_filter = ('status', 'project_type', 'company')
    search_fields = ('code', 'name', 'location', 'contract_number')


@admin.register(models.BOQItem)
class BOQItemAdmin(admin.ModelAdmin):
    list_display = ('item_number', 'section', 'unit', 'quantity', 'rate', 'amount', 'completed_quantity', 'completion_percent')
    search_fields = ('item_number', 'description')
    list_filter = ('section__project',)


@admin.register(models.BudgetItem)
class BudgetItemAdmin(admin.ModelAdmin):
    list_display = ('project', 'category', 'current_budget', 'actual_cost', 'committed_cost', 'variance')
    list_filter = ('category', 'project')


for model in [
    models.Department,
    models.BusinessPartner,
    models.ProjectTeamMember,
    models.Contract,
    models.BOQSection,
    models.Material,
    models.StockMovement,
    models.PurchaseRequest,
    models.PurchaseOrder,
    models.Activity,
    models.DailyReport,
    models.RFI,
    models.Variation,
    models.EOTApplication,
    models.PaymentCertificate,
    models.Invoice,
    models.Document,
    models.Risk,
    models.SafetyIncident,
    models.Defect,
    models.ProjectTask,
    models.ApprovalRequest,
    models.Notification,
    models.AuditLog,
]:
    admin.site.register(model)

# Register your models here.
