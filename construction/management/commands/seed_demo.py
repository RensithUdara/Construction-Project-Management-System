from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from construction import models


class Command(BaseCommand):
    help = 'Create demo users and construction-management sample data.'

    @transaction.atomic
    def handle(self, *args, **options):
        User = get_user_model()

        admin, created = User.objects.get_or_create(username='admin', defaults={
            'email': 'admin@example.com',
            'first_name': 'System',
            'last_name': 'Admin',
            'is_staff': True,
            'is_superuser': True,
        })
        if created:
            admin.set_password('admin123')
            admin.save()

        pm, _ = User.objects.get_or_create(username='pm', defaults={
            'email': 'pm@example.com',
            'first_name': 'Asha',
            'last_name': 'Perera',
        })
        pm.set_password('pm123')
        pm.save()

        qs, _ = User.objects.get_or_create(username='qs', defaults={
            'email': 'qs@example.com',
            'first_name': 'Nimal',
            'last_name': 'Fernando',
        })
        qs.set_password('qs123')
        qs.save()

        company, _ = models.Company.objects.get_or_create(
            name='ABC Construction',
            defaults={
                'registration_number': 'PV-2026-001',
                'email': 'info@abcconstruction.test',
                'phone': '+94 11 555 0100',
                'address': 'Colombo, Sri Lanka',
            },
        )

        departments = {}
        for name in ['Project Management', 'Engineering', 'Quantity Surveying', 'Procurement', 'Finance']:
            departments[name], _ = models.Department.objects.get_or_create(company=company, name=name)

        admin.profile.company = company
        admin.profile.role = models.Profile.Role.SYSTEM_ADMIN
        admin.profile.save()
        pm.profile.company = company
        pm.profile.department = departments['Project Management']
        pm.profile.role = models.Profile.Role.PROJECT_MANAGER
        pm.profile.save()
        qs.profile.company = company
        qs.profile.department = departments['Quantity Surveying']
        qs.profile.role = models.Profile.Role.QUANTITY_SURVEYOR
        qs.profile.save()

        client, _ = models.BusinessPartner.objects.get_or_create(
            company=company,
            partner_type=models.BusinessPartner.PartnerType.CLIENT,
            name='Oceanic Hotels PLC',
            defaults={'contact_person': 'Client Director', 'email': 'client@example.com'},
        )
        consultant, _ = models.BusinessPartner.objects.get_or_create(
            company=company,
            partner_type=models.BusinessPartner.PartnerType.CONSULTANT,
            name='Prime Consultants',
            defaults={'contact_person': 'Lead Architect', 'email': 'consultant@example.com'},
        )
        contractor, _ = models.BusinessPartner.objects.get_or_create(
            company=company,
            partner_type=models.BusinessPartner.PartnerType.CONTRACTOR,
            name='ABC Construction Main Works',
        )
        supplier, _ = models.BusinessPartner.objects.get_or_create(
            company=company,
            partner_type=models.BusinessPartner.PartnerType.SUPPLIER,
            name='Lanka Cement Suppliers',
            defaults={'payment_terms': '30 days', 'performance_score': 86},
        )

        project, _ = models.Project.objects.get_or_create(
            code='HOTEL-ABC',
            defaults={
                'company': company,
                'name': 'Hotel ABC',
                'description': 'Mixed-use hotel project with full commercial controls and site reporting.',
                'project_type': models.Project.ProjectType.HOTEL,
                'client': client,
                'consultant': consultant,
                'contractor': contractor,
                'location': 'Galle Face, Colombo',
                'contract_number': 'CNT-2026-001',
                'contract_value': Decimal('450000000.00'),
                'start_date': date(2026, 1, 15),
                'original_completion_date': date(2027, 6, 30),
                'status': models.Project.Status.CONSTRUCTION,
            },
        )

        models.ProjectTeamMember.objects.get_or_create(
            project=project,
            user=pm,
            project_role='Project Manager',
            defaults={'assigned_from': date(2026, 1, 1), 'responsibilities': 'Overall project delivery and reporting.'},
        )
        models.ProjectTeamMember.objects.get_or_create(
            project=project,
            user=qs,
            project_role='Quantity Surveyor',
            defaults={'assigned_from': date(2026, 1, 1), 'responsibilities': 'BOQ, valuations, variations, and payments.'},
        )

        models.Contract.objects.get_or_create(
            project=project,
            defaults={
                'contract_type': models.Contract.ContractType.LUMP_SUM,
                'framework': 'FIDIC',
                'contract_value': project.contract_value,
                'commencement_date': project.start_date,
                'completion_date': project.original_completion_date,
                'advance_payment': Decimal('45000000.00'),
                'payment_terms': 'Monthly interim payment certificates with retention.',
            },
        )

        section, _ = models.BOQSection.objects.get_or_create(project=project, code='03', defaults={'title': 'Concrete'})
        boq_items = [
            ('3.1', 'Grade 25 concrete to foundations', 'm3', '300', '28000', '210'),
            ('3.2', 'Reinforced concrete columns', 'm3', '120', '35000', '72'),
            ('3.3', 'Suspended slab concrete', 'm2', '1800', '4500', '900'),
        ]
        for number, desc, unit, qty, rate, complete in boq_items:
            models.BOQItem.objects.get_or_create(
                section=section,
                item_number=number,
                defaults={
                    'description': desc,
                    'unit': unit,
                    'quantity': Decimal(qty),
                    'rate': Decimal(rate),
                    'completed_quantity': Decimal(complete),
                },
            )

        budget_data = [
            (models.BudgetItem.Category.MATERIALS, '25000000', '23000000', '24000000'),
            (models.BudgetItem.Category.LABOUR, '12000000', '14000000', '14500000'),
            (models.BudgetItem.Category.EQUIPMENT, '5000000', '5500000', '5800000'),
            (models.BudgetItem.Category.SUBCONTRACTORS, '8000000', '6200000', '8100000'),
        ]
        for category, budget, actual, forecast in budget_data:
            models.BudgetItem.objects.get_or_create(
                project=project,
                category=category,
                defaults={
                    'original_budget': Decimal(budget),
                    'current_budget': Decimal(budget),
                    'actual_cost': Decimal(actual),
                    'committed_cost': Decimal(actual) * Decimal('1.08'),
                    'forecast_final_cost': Decimal(forecast),
                },
            )

        cement, _ = models.Material.objects.get_or_create(company=company, name='Cement', defaults={'category': 'Binder', 'unit': 'bags', 'minimum_stock': 250})
        models.StockMovement.objects.get_or_create(material=cement, reference='OPENING', defaults={'movement_type': models.StockMovement.MovementType.RECEIVE, 'quantity': 500, 'project': project})
        models.StockMovement.objects.get_or_create(material=cement, reference='GRN-001', defaults={'movement_type': models.StockMovement.MovementType.RECEIVE, 'quantity': 800, 'project': project})
        models.StockMovement.objects.get_or_create(material=cement, reference='ISS-001', defaults={'movement_type': models.StockMovement.MovementType.ISSUE, 'quantity': -350, 'project': project})

        pr, _ = models.PurchaseRequest.objects.get_or_create(
            request_number='PR-0001',
            defaults={'project': project, 'requested_by': pm, 'material': cement, 'description': 'Cement for slab pour.', 'quantity': 800, 'required_date': date.today() + timedelta(days=7), 'status': models.PurchaseRequest.Status.APPROVED},
        )
        models.PurchaseOrder.objects.get_or_create(
            po_number='PO-0001',
            defaults={'project': project, 'supplier': supplier, 'purchase_request': pr, 'order_date': date.today(), 'total_amount': Decimal('2250000'), 'status': models.PurchaseOrder.Status.ISSUED},
        )

        for code, name, start, end, progress, status in [
            ('A100', 'Site preparation', date(2026, 1, 15), date(2026, 2, 15), 100, models.Activity.Status.COMPLETE),
            ('A200', 'Foundation works', date(2026, 2, 16), date(2026, 5, 15), 92, models.Activity.Status.IN_PROGRESS),
            ('A300', 'Superstructure', date(2026, 5, 16), date(2026, 11, 30), 58, models.Activity.Status.IN_PROGRESS),
            ('A400', 'Finishing works', date(2026, 12, 1), date(2027, 5, 30), 5, models.Activity.Status.NOT_STARTED),
        ]:
            models.Activity.objects.get_or_create(project=project, code=code, defaults={'name': name, 'start_date': start, 'end_date': end, 'responsible_person': pm, 'progress': progress, 'status': status})

        models.DailyReport.objects.get_or_create(
            project=project,
            report_date=date(2026, 9, 25),
            defaults={'submitted_by': pm, 'weather': 'Sunny', 'workers_count': 76, 'equipment_summary': 'Tower crane, mixer, two dump trucks.', 'material_summary': 'Concrete and blockwork materials available.', 'work_completed': '120 m2 blockwork and 45 m3 concrete.', 'problems': 'Concrete delivery delayed by 2 hours.'},
        )
        models.RFI.objects.get_or_create(project=project, rfi_number='RFI-001', defaults={'subject': 'Beam opening clarification', 'question': 'Confirm MEP opening dimensions on level 04 beams.', 'priority': models.RFI.Priority.HIGH, 'due_date': date.today() + timedelta(days=3), 'status': models.RFI.Status.OPEN})
        models.Variation.objects.get_or_create(project=project, variation_number='VAR-001', defaults={'description': 'Additional lobby floor tile area.', 'reason': 'Client revised interior layout.', 'original_quantity': 1000, 'revised_quantity': 1250, 'rate': 4500, 'status': models.Variation.Status.SUBMITTED})
        models.EOTApplication.objects.get_or_create(project=project, eot_number='EOT-001', defaults={'delay_event': 'Heavy rain interruption', 'cause': 'Abnormal weather affected excavation.', 'start_date': date(2026, 5, 1), 'end_date': date(2026, 5, 5), 'submitted_by': pm, 'status': models.EOTApplication.Status.UNDER_REVIEW})
        models.PaymentCertificate.objects.get_or_create(project=project, certificate_number='IPC-001', defaults={'gross_amount': 10000000, 'previous_payment': 0, 'retention': 500000, 'advance_recovery': 300000, 'deductions': 100000, 'status': models.PaymentCertificate.Status.APPROVED})
        models.Document.objects.get_or_create(project=project, title='Structural Drawing Level 04', version='Rev 04', defaults={'category': models.Document.Category.DRAWING, 'uploaded_by': qs, 'status': models.Document.Status.APPROVED})
        models.Risk.objects.get_or_create(project=project, title='Material shortage', defaults={'category': 'Procurement', 'probability': models.Risk.Level.HIGH, 'impact': models.Risk.Level.HIGH, 'owner': pm, 'mitigation': 'Confirm long-lead orders two months ahead.', 'status': models.Risk.Status.OPEN})
        models.SafetyIncident.objects.get_or_create(project=project, incident_date=date(2026, 9, 20), title='PPE violation at slab edge', defaults={'severity': models.SafetyIncident.Severity.MEDIUM, 'description': 'Worker entered restricted edge zone without harness.', 'corrective_action': 'Toolbox meeting completed.'})
        models.Defect.objects.get_or_create(project=project, defect_number='DEF-001', defaults={'location': 'Room 203', 'description': 'Painting surface defect.', 'category': 'Finishing', 'priority': models.RFI.Priority.MEDIUM, 'assigned_to': pm, 'due_date': date.today() + timedelta(days=14), 'status': models.Defect.Status.ASSIGNED})
        models.ProjectTask.objects.get_or_create(project=project, title='Submit weekly progress report', defaults={'description': 'Compile site progress and cost highlights.', 'assignee': pm, 'priority': models.RFI.Priority.HIGH, 'due_date': date.today() + timedelta(days=2), 'status': models.ProjectTask.Status.IN_PROGRESS})
        models.ApprovalRequest.objects.get_or_create(project=project, title='Approve PR-0001', defaults={'target_model': 'PurchaseRequest', 'target_id': pr.id, 'requested_by': pm, 'approver': admin})

        self.stdout.write(self.style.SUCCESS('Demo data ready. Login: admin / admin123 or pm / pm123'))
