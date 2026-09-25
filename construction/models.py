from decimal import Decimal

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Company(TimeStampedModel):
    name = models.CharField(max_length=200)
    registration_number = models.CharField(max_length=80, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=40, blank=True)
    address = models.TextField(blank=True)
    logo = models.ImageField(upload_to='company-logos/', blank=True)

    class Meta:
        verbose_name_plural = 'companies'
        ordering = ['name']

    def __str__(self):
        return self.name


class Department(TimeStampedModel):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='departments')
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)

    class Meta:
        unique_together = ('company', 'name')
        ordering = ['company__name', 'name']

    def __str__(self):
        return f'{self.company} - {self.name}'


class Profile(TimeStampedModel):
    class Role(models.TextChoices):
        SYSTEM_ADMIN = 'system_admin', 'System Administrator'
        COMPANY_ADMIN = 'company_admin', 'Company Admin'
        PROJECT_MANAGER = 'project_manager', 'Project Manager'
        QUANTITY_SURVEYOR = 'quantity_surveyor', 'Quantity Surveyor'
        SITE_ENGINEER = 'site_engineer', 'Site Engineer'
        PROCUREMENT = 'procurement', 'Procurement Officer'
        FINANCE = 'finance', 'Finance Officer'
        CONSULTANT = 'consultant', 'Consultant'
        CONTRACTOR = 'contractor', 'Contractor'

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True, blank=True, related_name='profiles')
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    role = models.CharField(max_length=40, choices=Role.choices, default=Role.SITE_ENGINEER)
    designation = models.CharField(max_length=120, blank=True)
    phone = models.CharField(max_length=40, blank=True)

    def __str__(self):
        return f'{self.user.get_full_name() or self.user.username} ({self.get_role_display()})'


class BusinessPartner(TimeStampedModel):
    class PartnerType(models.TextChoices):
        CLIENT = 'client', 'Client'
        CONSULTANT = 'consultant', 'Consultant'
        CONTRACTOR = 'contractor', 'Contractor'
        SUPPLIER = 'supplier', 'Supplier'
        SUBCONTRACTOR = 'subcontractor', 'Subcontractor'

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='partners')
    partner_type = models.CharField(max_length=30, choices=PartnerType.choices)
    name = models.CharField(max_length=200)
    contact_person = models.CharField(max_length=120, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=40, blank=True)
    address = models.TextField(blank=True)
    payment_terms = models.CharField(max_length=200, blank=True)
    performance_score = models.PositiveSmallIntegerField(default=80, validators=[MinValueValidator(0), MaxValueValidator(100)])

    class Meta:
        ordering = ['partner_type', 'name']

    def __str__(self):
        return self.name


class Project(TimeStampedModel):
    class ProjectType(models.TextChoices):
        RESIDENTIAL = 'residential', 'Residential'
        COMMERCIAL = 'commercial', 'Commercial'
        HOTEL = 'hotel', 'Hotel'
        HOSPITAL = 'hospital', 'Hospital'
        SCHOOL = 'school', 'School'
        ROAD = 'road', 'Road'
        BRIDGE = 'bridge', 'Bridge'
        INDUSTRIAL = 'industrial', 'Industrial'
        INFRASTRUCTURE = 'infrastructure', 'Infrastructure'

    class Status(models.TextChoices):
        PLANNING = 'planning', 'Planning'
        TENDER = 'tender', 'Tender'
        AWARDED = 'awarded', 'Awarded'
        MOBILIZATION = 'mobilization', 'Mobilization'
        CONSTRUCTION = 'construction', 'Construction'
        PRACTICAL_COMPLETION = 'practical_completion', 'Practical Completion'
        DEFECTS_LIABILITY = 'defects_liability', 'Defects Liability'
        FINAL_COMPLETION = 'final_completion', 'Final Completion'

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='projects')
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=40, unique=True)
    description = models.TextField(blank=True)
    project_type = models.CharField(max_length=40, choices=ProjectType.choices)
    client = models.ForeignKey(BusinessPartner, on_delete=models.SET_NULL, null=True, blank=True, related_name='client_projects')
    consultant = models.ForeignKey(BusinessPartner, on_delete=models.SET_NULL, null=True, blank=True, related_name='consultant_projects')
    contractor = models.ForeignKey(BusinessPartner, on_delete=models.SET_NULL, null=True, blank=True, related_name='contractor_projects')
    location = models.CharField(max_length=250, blank=True)
    contract_number = models.CharField(max_length=80, blank=True)
    contract_value = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    start_date = models.DateField(null=True, blank=True)
    original_completion_date = models.DateField(null=True, blank=True)
    revised_completion_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=40, choices=Status.choices, default=Status.PLANNING)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.code} - {self.name}'

    def get_absolute_url(self):
        return reverse('project_detail', args=[self.pk])

    @property
    def budget_total(self):
        return self.budget_items.aggregate(total=models.Sum('current_budget'))['total'] or Decimal('0')

    @property
    def actual_total(self):
        return self.budget_items.aggregate(total=models.Sum('actual_cost'))['total'] or Decimal('0')

    @property
    def progress_percent(self):
        avg = self.activities.aggregate(avg=models.Avg('progress'))['avg']
        return round(avg or 0, 1)


class ProjectTeamMember(TimeStampedModel):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='team_members')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    project_role = models.CharField(max_length=120)
    responsibilities = models.TextField(blank=True)
    assigned_from = models.DateField()
    assigned_to = models.DateField(null=True, blank=True)
    active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('project', 'user', 'project_role')
        ordering = ['project', 'project_role']

    def __str__(self):
        return f'{self.user} - {self.project_role}'


class Contract(TimeStampedModel):
    class ContractType(models.TextChoices):
        LUMP_SUM = 'lump_sum', 'Lump Sum'
        UNIT_RATE = 'unit_rate', 'Unit Rate'
        COST_PLUS = 'cost_plus', 'Cost Plus'
        DESIGN_BUILD = 'design_build', 'Design & Build'
        EPC = 'epc', 'EPC'

    project = models.OneToOneField(Project, on_delete=models.CASCADE, related_name='contract')
    contract_type = models.CharField(max_length=30, choices=ContractType.choices)
    framework = models.CharField(max_length=40, blank=True, help_text='FIDIC, SBD, NEC, or custom')
    contract_value = models.DecimalField(max_digits=16, decimal_places=2)
    commencement_date = models.DateField(null=True, blank=True)
    completion_date = models.DateField(null=True, blank=True)
    retention_percent = models.DecimalField(max_digits=5, decimal_places=2, default=5)
    advance_payment = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    payment_terms = models.TextField(blank=True)
    defects_liability_days = models.PositiveIntegerField(default=365)
    liquidated_damages = models.DecimalField(max_digits=16, decimal_places=2, default=0)

    def __str__(self):
        return f'Contract {self.project.code}'


class BOQSection(TimeStampedModel):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='boq_sections')
    code = models.CharField(max_length=20)
    title = models.CharField(max_length=200)

    class Meta:
        unique_together = ('project', 'code')
        ordering = ['project', 'code']

    def __str__(self):
        return f'{self.code} {self.title}'

    @property
    def total_amount(self):
        return sum((item.amount for item in self.items.all()), Decimal('0'))


class BOQItem(TimeStampedModel):
    section = models.ForeignKey(BOQSection, on_delete=models.CASCADE, related_name='items')
    item_number = models.CharField(max_length=40)
    description = models.TextField()
    unit = models.CharField(max_length=30)
    quantity = models.DecimalField(max_digits=14, decimal_places=3)
    rate = models.DecimalField(max_digits=14, decimal_places=2)
    completed_quantity = models.DecimalField(max_digits=14, decimal_places=3, default=0)

    class Meta:
        unique_together = ('section', 'item_number')
        ordering = ['section__code', 'item_number']

    def __str__(self):
        return f'{self.item_number} - {self.description[:40]}'

    @property
    def amount(self):
        return self.quantity * self.rate

    @property
    def remaining_quantity(self):
        return max(self.quantity - self.completed_quantity, Decimal('0'))

    @property
    def completion_percent(self):
        if not self.quantity:
            return 0
        return round((self.completed_quantity / self.quantity) * 100, 2)


class BudgetItem(TimeStampedModel):
    class Category(models.TextChoices):
        MATERIALS = 'materials', 'Materials'
        LABOUR = 'labour', 'Labour'
        EQUIPMENT = 'equipment', 'Equipment'
        SUBCONTRACTORS = 'subcontractors', 'Subcontractors'
        TRANSPORT = 'transport', 'Transportation'
        OVERHEADS = 'overheads', 'Overheads'
        CONTINGENCY = 'contingency', 'Contingency'
        PROFIT = 'profit', 'Profit'

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='budget_items')
    category = models.CharField(max_length=40, choices=Category.choices)
    original_budget = models.DecimalField(max_digits=16, decimal_places=2)
    current_budget = models.DecimalField(max_digits=16, decimal_places=2)
    actual_cost = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    committed_cost = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    forecast_final_cost = models.DecimalField(max_digits=16, decimal_places=2, default=0)

    class Meta:
        unique_together = ('project', 'category')

    @property
    def variance(self):
        return self.current_budget - self.actual_cost

    def __str__(self):
        return f'{self.project.code} - {self.get_category_display()}'


class Material(TimeStampedModel):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='materials')
    name = models.CharField(max_length=160)
    category = models.CharField(max_length=120, blank=True)
    unit = models.CharField(max_length=30)
    minimum_stock = models.DecimalField(max_digits=14, decimal_places=3, default=0)

    class Meta:
        unique_together = ('company', 'name')
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def current_stock(self):
        return self.stock_movements.aggregate(total=models.Sum('quantity'))['total'] or Decimal('0')


class StockMovement(TimeStampedModel):
    class MovementType(models.TextChoices):
        RECEIVE = 'receive', 'Receive'
        ISSUE = 'issue', 'Issue'
        RETURN = 'return', 'Return'
        ADJUST = 'adjust', 'Adjustment'
        TRANSFER = 'transfer', 'Transfer'

    material = models.ForeignKey(Material, on_delete=models.CASCADE, related_name='stock_movements')
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, blank=True, related_name='stock_movements')
    movement_type = models.CharField(max_length=20, choices=MovementType.choices)
    quantity = models.DecimalField(max_digits=14, decimal_places=3, help_text='Use negative values for issues or reductions.')
    reference = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f'{self.material} {self.quantity}'


class PurchaseRequest(TimeStampedModel):
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        SUBMITTED = 'submitted', 'Submitted'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'
        ORDERED = 'ordered', 'Ordered'

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='purchase_requests')
    request_number = models.CharField(max_length=60, unique=True)
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    material = models.ForeignKey(Material, on_delete=models.SET_NULL, null=True, blank=True)
    description = models.TextField()
    quantity = models.DecimalField(max_digits=14, decimal_places=3, default=1)
    required_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)

    def __str__(self):
        return self.request_number


class PurchaseOrder(TimeStampedModel):
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        ISSUED = 'issued', 'Issued'
        PART_RECEIVED = 'part_received', 'Part Received'
        RECEIVED = 'received', 'Received'
        CLOSED = 'closed', 'Closed'

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='purchase_orders')
    po_number = models.CharField(max_length=60, unique=True)
    supplier = models.ForeignKey(BusinessPartner, on_delete=models.PROTECT, limit_choices_to={'partner_type': BusinessPartner.PartnerType.SUPPLIER})
    purchase_request = models.ForeignKey(PurchaseRequest, on_delete=models.SET_NULL, null=True, blank=True)
    order_date = models.DateField(null=True, blank=True)
    total_amount = models.DecimalField(max_digits=16, decimal_places=2)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)

    def __str__(self):
        return self.po_number


class Activity(TimeStampedModel):
    class Status(models.TextChoices):
        NOT_STARTED = 'not_started', 'Not Started'
        IN_PROGRESS = 'in_progress', 'In Progress'
        DELAYED = 'delayed', 'Delayed'
        COMPLETE = 'complete', 'Complete'

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='activities')
    code = models.CharField(max_length=40)
    name = models.CharField(max_length=200)
    start_date = models.DateField()
    end_date = models.DateField()
    responsible_person = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    dependencies = models.ManyToManyField('self', symmetrical=False, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NOT_STARTED)
    progress = models.PositiveSmallIntegerField(default=0, validators=[MaxValueValidator(100)])

    class Meta:
        unique_together = ('project', 'code')
        ordering = ['start_date']

    def __str__(self):
        return f'{self.code} - {self.name}'


class DailyReport(TimeStampedModel):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='daily_reports')
    report_date = models.DateField()
    submitted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    weather = models.CharField(max_length=80, blank=True)
    workers_count = models.PositiveIntegerField(default=0)
    equipment_summary = models.TextField(blank=True)
    material_summary = models.TextField(blank=True)
    work_completed = models.TextField()
    problems = models.TextField(blank=True)
    safety_incidents = models.TextField(blank=True)
    comments = models.TextField(blank=True)

    class Meta:
        unique_together = ('project', 'report_date')
        ordering = ['-report_date']

    def __str__(self):
        return f'{self.project.code} - {self.report_date}'


class RFI(TimeStampedModel):
    class Priority(models.TextChoices):
        LOW = 'low', 'Low'
        MEDIUM = 'medium', 'Medium'
        HIGH = 'high', 'High'
        CRITICAL = 'critical', 'Critical'

    class Status(models.TextChoices):
        OPEN = 'open', 'Open'
        UNDER_REVIEW = 'under_review', 'Under Review'
        RESPONDED = 'responded', 'Responded'
        CLOSED = 'closed', 'Closed'

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='rfis')
    rfi_number = models.CharField(max_length=60, unique=True)
    subject = models.CharField(max_length=220)
    question = models.TextField()
    activity = models.ForeignKey(Activity, on_delete=models.SET_NULL, null=True, blank=True)
    drawing_reference = models.CharField(max_length=120, blank=True)
    priority = models.CharField(max_length=20, choices=Priority.choices, default=Priority.MEDIUM)
    due_date = models.DateField(null=True, blank=True)
    response = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)

    def __str__(self):
        return self.rfi_number


class Variation(TimeStampedModel):
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        SUBMITTED = 'submitted', 'Submitted'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='variations')
    variation_number = models.CharField(max_length=60, unique=True)
    description = models.TextField()
    reason = models.TextField(blank=True)
    original_quantity = models.DecimalField(max_digits=14, decimal_places=3, default=0)
    revised_quantity = models.DecimalField(max_digits=14, decimal_places=3, default=0)
    rate = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    time_impact_days = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)

    @property
    def additional_cost(self):
        return (self.revised_quantity - self.original_quantity) * self.rate

    def __str__(self):
        return self.variation_number


class EOTApplication(TimeStampedModel):
    class Status(models.TextChoices):
        SUBMITTED = 'submitted', 'Submitted'
        UNDER_REVIEW = 'under_review', 'Under Review'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='eot_applications')
    eot_number = models.CharField(max_length=60, unique=True)
    delay_event = models.CharField(max_length=220)
    cause = models.TextField()
    start_date = models.DateField()
    end_date = models.DateField()
    submitted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    consultant_review = models.TextField(blank=True)
    revised_completion_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SUBMITTED)

    @property
    def delay_duration(self):
        return (self.end_date - self.start_date).days + 1

    def __str__(self):
        return self.eot_number


class PaymentCertificate(TimeStampedModel):
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        SUBMITTED = 'submitted', 'Submitted'
        APPROVED = 'approved', 'Approved'
        PAID = 'paid', 'Paid'

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='payment_certificates')
    certificate_number = models.CharField(max_length=60, unique=True)
    gross_amount = models.DecimalField(max_digits=16, decimal_places=2)
    previous_payment = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    retention = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    advance_recovery = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    deductions = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)

    @property
    def current_payment(self):
        return self.gross_amount - self.previous_payment

    @property
    def net_amount(self):
        return self.current_payment - self.retention - self.advance_recovery - self.deductions

    def __str__(self):
        return self.certificate_number


class Invoice(TimeStampedModel):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        APPROVED = 'approved', 'Approved'
        PAID = 'paid', 'Paid'
        REJECTED = 'rejected', 'Rejected'

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='invoices')
    supplier = models.ForeignKey(BusinessPartner, on_delete=models.PROTECT)
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.SET_NULL, null=True, blank=True)
    invoice_number = models.CharField(max_length=80, unique=True)
    invoice_date = models.DateField()
    amount = models.DecimalField(max_digits=16, decimal_places=2)
    tax = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    due_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)

    @property
    def total(self):
        return self.amount + self.tax

    def __str__(self):
        return self.invoice_number


class Document(TimeStampedModel):
    class Category(models.TextChoices):
        CONTRACT = 'contract', 'Contract'
        DRAWING = 'drawing', 'Drawing'
        BOQ = 'boq', 'BOQ'
        SPECIFICATION = 'specification', 'Specification'
        REPORT = 'report', 'Report'
        CERTIFICATE = 'certificate', 'Certificate'
        INVOICE = 'invoice', 'Invoice'
        RFI = 'rfi', 'RFI'
        EOT = 'eot', 'EOT'
        VARIATION = 'variation', 'Variation'

    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        SUBMITTED = 'submitted', 'Submitted'
        UNDER_REVIEW = 'under_review', 'Under Review'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='documents')
    title = models.CharField(max_length=220)
    category = models.CharField(max_length=40, choices=Category.choices)
    version = models.CharField(max_length=30, default='Rev 01')
    file = models.FileField(upload_to='documents/', blank=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    is_current = models.BooleanField(default=True)

    class Meta:
        ordering = ['project', 'title', '-created_at']

    def __str__(self):
        return f'{self.title} {self.version}'


class Risk(TimeStampedModel):
    class Level(models.TextChoices):
        LOW = 'low', 'Low'
        MEDIUM = 'medium', 'Medium'
        HIGH = 'high', 'High'

    class Status(models.TextChoices):
        OPEN = 'open', 'Open'
        MONITORING = 'monitoring', 'Monitoring'
        CLOSED = 'closed', 'Closed'

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='risks')
    title = models.CharField(max_length=220)
    category = models.CharField(max_length=120, blank=True)
    probability = models.CharField(max_length=20, choices=Level.choices)
    impact = models.CharField(max_length=20, choices=Level.choices)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    mitigation = models.TextField(blank=True)
    due_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)

    @property
    def risk_score(self):
        values = {'low': 1, 'medium': 2, 'high': 3}
        return values[self.probability] * values[self.impact]

    def __str__(self):
        return self.title


class SafetyIncident(TimeStampedModel):
    class Severity(models.TextChoices):
        LOW = 'low', 'Low'
        MEDIUM = 'medium', 'Medium'
        HIGH = 'high', 'High'
        CRITICAL = 'critical', 'Critical'

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='safety_incidents')
    incident_date = models.DateField()
    title = models.CharField(max_length=220)
    severity = models.CharField(max_length=20, choices=Severity.choices)
    description = models.TextField()
    corrective_action = models.TextField(blank=True)
    closed = models.BooleanField(default=False)

    def __str__(self):
        return self.title


class Defect(TimeStampedModel):
    class Status(models.TextChoices):
        OPEN = 'open', 'Open'
        ASSIGNED = 'assigned', 'Assigned'
        RECTIFIED = 'rectified', 'Rectified'
        VERIFIED = 'verified', 'Verified'
        CLOSED = 'closed', 'Closed'

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='defects')
    defect_number = models.CharField(max_length=60, unique=True)
    location = models.CharField(max_length=180)
    description = models.TextField()
    category = models.CharField(max_length=120, blank=True)
    priority = models.CharField(max_length=20, choices=RFI.Priority.choices, default=RFI.Priority.MEDIUM)
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)
    rectification = models.TextField(blank=True)
    verification = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)

    def __str__(self):
        return self.defect_number


class ProjectTask(TimeStampedModel):
    class Status(models.TextChoices):
        TODO = 'todo', 'To Do'
        IN_PROGRESS = 'in_progress', 'In Progress'
        BLOCKED = 'blocked', 'Blocked'
        UNDER_REVIEW = 'under_review', 'Under Review'
        COMPLETED = 'completed', 'Completed'

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(max_length=220)
    description = models.TextField(blank=True)
    assignee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    priority = models.CharField(max_length=20, choices=RFI.Priority.choices, default=RFI.Priority.MEDIUM)
    start_date = models.DateField(null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.TODO)

    def __str__(self):
        return self.title


class ApprovalRequest(TimeStampedModel):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='approval_requests')
    title = models.CharField(max_length=220)
    target_model = models.CharField(max_length=80)
    target_id = models.PositiveIntegerField()
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='requested_approvals')
    approver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_approvals')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    comments = models.TextField(blank=True)

    def __str__(self):
        return self.title


class Notification(TimeStampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=180)
    message = models.TextField()
    link = models.CharField(max_length=250, blank=True)
    read = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class AuditLog(TimeStampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=80)
    model_name = models.CharField(max_length=80)
    object_id = models.CharField(max_length=80, blank=True)
    summary = models.TextField()
    old_value = models.TextField(blank=True)
    new_value = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.action} {self.model_name}'

# Create your models here.
