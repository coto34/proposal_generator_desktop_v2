from typing import Dict, List
import re


class InternationalBudgetGenerator:
    """Enhanced budget generator with international development standards"""
    
    def __init__(self, project_info: Dict, tor_content: str):
        self.project = project_info
        self.tor_content = tor_content
        self.donor_standards = self._load_donor_standards()
        self.guatemala_costs = self._load_guatemala_cost_database()
        
    def _load_donor_standards(self) -> Dict:
        """Load donor-specific budget standards and requirements"""
        return {
            "USAID": {
                "indirect_cost_rate": 0.10,  # 10% max
                "required_categories": [
                    "Personnel", "Fringe Benefits", "Travel", "Equipment",
                    "Supplies", "Contractual", "Other Direct Costs", "Indirect Costs"
                ],
                "cost_principles": "2 CFR 200 - Uniform Administrative Requirements",
                "audit_requirements": "Single Audit Act compliance",
                "reporting": "SF-425 Federal Financial Reports"
            },
            "BID": {
                "indirect_cost_rate": 0.08,  # 8% típico
                "required_categories": [
                    "Recursos Humanos", "Consultorías", "Viajes y Viáticos",
                    "Equipamiento", "Materiales e Insumos", "Servicios",
                    "Gastos de Funcionamiento", "Auditorías"
                ],
                "cost_principles": "Políticas de Adquisiciones del BID",
                "audit_requirements": "Auditoría externa anual obligatoria",
                "reporting": "Informes financieros trimestrales PMR"
            },
            "GIZ": {
                "indirect_cost_rate": 0.07,
                "required_categories": [
                    "Personal", "Viajes", "Material/Equipos", "Servicios Externos",
                    "Costos Operativos", "Overhead Institucional"
                ],
                "cost_principles": "GIZ Procurement Guidelines",
                "audit_requirements": "Verificación financiera GIZ",
                "reporting": "Reportes según COMPASS system"
            }
        }
    
    def _load_guatemala_cost_database(self) -> Dict:
        """Load Guatemala-specific cost database with market rates"""
        return {
            "salaries": {
                # Salarios profesionales en Guatemala (USD mensual)
                "project_coordinator_senior": {"min": 2800, "max": 3500, "average": 3150},
                "project_coordinator_junior": {"min": 1800, "max": 2200, "average": 2000},
                "technical_specialist": {"min": 2200, "max": 2800, "average": 2500},
                "community_facilitator": {"min": 800, "max": 1200, "average": 1000},
                "administrative_assistant": {"min": 600, "max": 900, "average": 750},
                "accountant": {"min": 1200, "max": 1800, "average": 1500},
                "driver": {"min": 500, "max": 700, "average": 600},
                "security_guard": {"min": 400, "max": 600, "average": 500}
            },
            "benefits": {
                # Prestaciones laborales Guatemala (% del salario base)
                "social_security": 0.1267,  # IGSS patronal
                "bonus_14": 0.0833,  # Bono 14 anual
                "aguinaldo": 0.0833,  # Aguinaldo anual  
                "vacation": 0.0417,  # Vacaciones
                "indemnification": 0.0833,  # Indemnización
                "total_benefits": 0.4183  # 41.83% total
            },
            "travel": {
                # Costos de viaje por región
                "per_diem_guatemala_city": 75,  # USD/día
                "per_diem_regional_center": 65,  # USD/día
                "per_diem_rural_area": 45,     # USD/día
                "transport_per_km": 0.35,      # USD/km
                "accommodation_capital": 85,    # USD/noche
                "accommodation_regional": 55,   # USD/noche
                "accommodation_rural": 35,      # USD/noche
            },
            "equipment": {
                # Precios de equipamiento en Guatemala
                "laptop_standard": 800,
                "laptop_advanced": 1200,
                "printer_multifunction": 450,
                "projector_portable": 650,
                "vehicle_pickup_used": 25000,
                "vehicle_pickup_new": 35000,
                "motorcycle": 2500,
                "smartphone": 300,
                "tablet": 400,
                "gps_device": 200
            },
            "services": {
                # Servicios profesionales Guatemala
                "external_audit": {"min": 3500, "max": 8000, "average": 5500},
                "legal_services_hourly": 45,
                "translation_per_page": 8,
                "web_design": {"min": 800, "max": 2500, "average": 1500},
                "training_facilitator_day": 200,
                "event_management_day": 150
            },
            "operational": {
                # Costos operativos mensuales
                "office_rent_guatemala_city": {"min": 800, "max": 1500, "per_m2": 12},
                "office_rent_regional": {"min": 400, "max": 800, "per_m2": 8},
                "internet_office": 80,
                "telephone_mobile": 25,
                "electricity_monthly": {"min": 150, "max": 400},
                "water_monthly": {"min": 30, "max": 80},
                "office_supplies_monthly": 120,
                "fuel_gallon": 3.2,
                "vehicle_maintenance_monthly": 180
            }
        }
    
    def generate_comprehensive_budget(self) -> Dict:
        """Generate comprehensive budget following international standards"""
        
        # 1. Extract activities from ToR using AI analysis
        activities = self._extract_activities_from_tor()
        
        # 2. Build detailed budget structure
        budget_items = []
        
        # 2.1 Personnel (typically 50-70% of budget)
        personnel_items = self._generate_personnel_budget(activities)
        budget_items.extend(personnel_items)
        
        # 2.2 Equipment and supplies (typically 10-20% of budget)
        equipment_items = self._generate_equipment_budget(activities)
        budget_items.extend(equipment_items)
        
        # 2.3 Travel and transportation (typically 5-15% of budget)
        travel_items = self._generate_travel_budget(activities)
        budget_items.extend(travel_items)
        
        # 2.4 Training and events (typically 10-25% of budget)
        training_items = self._generate_training_budget(activities)
        budget_items.extend(training_items)
        
        # 2.5 Services and operations (typically 5-15% of budget)
        services_items = self._generate_services_budget(activities)
        budget_items.extend(services_items)
        
        # 3. Calculate totals and apply donor standards
        donor = self.project.get('donor', 'BID')
        standards = self.donor_standards.get(donor, self.donor_standards['BID'])
        
        subtotal = sum(item['total_cost'] for item in budget_items)
        indirect_costs = subtotal * standards['indirect_cost_rate']
        total_budget = subtotal + indirect_costs
        
        # 4. Generate comprehensive budget structure
        return {
            "currency": "USD",
            "exchange_rate_gtq": 7.75,
            "project_duration_months": self.project.get('duration_months', 24),
            "donor_standards": standards,
            
            # Detailed line items
            "items": budget_items,
            
            # Activity-based breakdown
            "activity_breakdown": self._generate_activity_breakdown(activities, budget_items),
            
            # Financial summary
            "financial_summary": {
                "direct_costs": subtotal,
                "indirect_costs": indirect_costs,
                "indirect_rate": standards['indirect_cost_rate'],
                "total_budget": total_budget,
                "cost_per_beneficiary": self._calculate_cost_per_beneficiary(total_budget),
                "budget_efficiency_indicators": self._calculate_efficiency_indicators(total_budget)
            },
            
            # Category breakdown
            "category_breakdown": self._generate_category_breakdown(budget_items),
            
            # Timeline and cash flow
            "timeline_breakdown": self._generate_timeline_breakdown(activities, budget_items),
            
            # Geographic breakdown
            "geographic_breakdown": self._generate_geographic_breakdown(budget_items),
            
            # Risk and contingency analysis
            "risk_analysis": self._generate_risk_analysis(budget_items),
            
            # Compliance framework
            "compliance": {
                "donor_requirements": self._validate_donor_compliance(budget_items, standards),
                "guatemala_regulations": self._validate_guatemala_compliance(budget_items),
                "audit_requirements": standards.get('audit_requirements', 'Annual external audit')
            },
            
            # Performance indicators
            "performance_indicators": self._generate_budget_kpis(total_budget),
            
            # Gantt chart data
            "gantt_data": self._generate_gantt_data(activities)
        }
    
    def _extract_activities_from_tor(self) -> List[Dict]:
        """Extract and structure activities from ToR content using AI analysis"""
        # This would typically use an LLM to intelligently extract activities
        # For now, providing a structured approach
        
        activities = [
            {
                "code": "A1.1",
                "name": "Diagnóstico participativo comunitario",
                "component": "Fortalecimiento organizacional",
                "duration_months": 3,
                "start_month": 1,
                "end_month": 3,
                "complexity": "high",
                "geographic_scope": "all_locations",
                "personnel_required": ["coordinator", "facilitators", "technical_specialist"],
                "equipment_needed": ["vehicles", "laptops", "tablets"],
                "travel_intensive": True,
                "training_component": True
            },
            {
                "code": "A1.2", 
                "name": "Diseño participativo de planes comunitarios",
                "component": "Fortalecimiento organizacional",
                "duration_months": 4,
                "start_month": 3,
                "end_month": 6,
                "complexity": "high",
                "geographic_scope": "all_locations",
                "personnel_required": ["coordinator", "facilitators", "technical_specialist"],
                "equipment_needed": ["laptops", "projector"],
                "travel_intensive": True,
                "training_component": True
            }
            # Additional activities would be extracted from ToR content
        ]
        
        return activities
    
    def _generate_personnel_budget(self, activities: List[Dict]) -> List[Dict]:
        """Generate detailed personnel budget based on activities"""
        personnel_items = []
        costs = self.guatemala_costs['salaries']
        benefits_rate = self.guatemala_costs['benefits']['total_benefits']
        
        # Core team positions
        core_positions = [
            {
                "position": "Coordinador de Proyecto",
                "code": "P001",
                "salary_category": "project_coordinator_senior",
                "percentage_time": 100,
                "months": self.project.get('duration_months', 24),
                "justification": "Coordinación general y supervisión técnica del proyecto"
            },
            {
                "position": "Especialista Técnico",
                "code": "P002", 
                "salary_category": "technical_specialist",
                "percentage_time": 100,
                "months": self.project.get('duration_months', 24),
                "justification": "Asesoría técnica especializada y desarrollo metodológico"
            },
            {
                "position": "Facilitadores Comunitarios",
                "code": "P003",
                "salary_category": "community_facilitator", 
                "quantity": 4,
                "percentage_time": 100,
                "months": 20,  # No todo el proyecto
                "justification": "Trabajo directo con comunidades y organizaciones locales"
            }
        ]
        
        for position in core_positions:
            base_salary = costs[position['salary_category']]['average']
            quantity = position.get('quantity', 1)
            
            # Calculate gross salary including benefits
            monthly_gross = base_salary * (1 + benefits_rate)
            total_cost = monthly_gross * position['months'] * quantity * (position['percentage_time']/100)
            
            personnel_items.append({
                "item_code": position['code'],
                "activity_code": "ALL",  # Core staff works across activities
                "category": "Personal Técnico y Profesional",
                "subcategory": position['position'],
                "description": f"{position['position']} - {position['justification']}",
                "unit": "mes-persona",
                "quantity": position['months'] * quantity,
                "unit_cost": monthly_gross,
                "total_cost": total_cost,
                "cost_breakdown": {
                    "base_salary": base_salary * position['months'] * quantity,
                    "benefits": base_salary * position['months'] * quantity * benefits_rate,
                    "total": total_cost
                },
                "procurement_method": "Contratación directa",
                "justification": position['justification'],
                "donor_eligible": True,
                "phase": "Implementación"
            })
        
        return personnel_items
    
    def _generate_gantt_data(self, activities: List[Dict]) -> Dict:
        """Generate Gantt chart data structure"""
        gantt_data = {
            "project_start": "2024-01-01",  # Would be dynamic
            "project_end": "2025-12-31",   # Would be calculated
            "activities": [],
            "milestones": [],
            "dependencies": []
        }
        
        for activity in activities:
            gantt_activity = {
                "id": activity['code'],
                "name": activity['name'],
                "component": activity['component'],
                "start_date": f"2024-{activity['start_month']:02d}-01",
                "duration_months": activity['duration_months'],
                "end_date": f"2024-{activity['end_month']:02d}-30",
                "progress": 0,
                "responsible": "IEPADES",
                "budget_allocated": 0,  # Would be calculated from budget items
                "critical_path": activity.get('critical_path', False)
            }
            gantt_data["activities"].append(gantt_activity)
        
        # Add key milestones
        milestones = [
            {"name": "Inicio de proyecto", "date": "2024-01-01", "type": "start"},
            {"name": "Diagnóstico completado", "date": "2024-03-31", "type": "deliverable"},
            {"name": "Evaluación de medio término", "date": "2024-12-31", "type": "evaluation"},
            {"name": "Finalización de proyecto", "date": "2025-12-31", "type": "end"}
        ]
        gantt_data["milestones"] = milestones
        
        return gantt_data
    
    def _calculate_cost_per_beneficiary(self, total_budget: float) -> Dict:
        """Calculate cost efficiency indicators"""
        direct_ben = self._parse_beneficiaries(self.project.get('beneficiaries_direct', '0'))
        indirect_ben = self._parse_beneficiaries(self.project.get('beneficiaries_indirect', '0'))
        
        return {
            "cost_per_direct_beneficiary": total_budget / max(direct_ben, 1),
            "cost_per_total_beneficiary": total_budget / max(direct_ben + indirect_ben, 1),
            "cost_effectiveness_rating": self._assess_cost_effectiveness(total_budget, direct_ben)
        }
    
    def _parse_beneficiaries(self, beneficiaries_str: str) -> int:
        """Parse beneficiaries string to number"""
        import re
        numbers = re.findall(r'\d+', str(beneficiaries_str).replace(',', ''))
        return int(numbers[0]) if numbers else 0
    
    def _generate_activity_breakdown(self, activities: List[Dict], budget_items: List[Dict]) -> List[Dict]:
        """Generate detailed breakdown by activity"""
        activity_breakdown = []
        
        for activity in activities:
            related_items = [item for item in budget_items 
                           if item.get('activity_code') == activity['code'] or item.get('activity_code') == 'ALL']
            
            total_cost = sum(item['total_cost'] for item in related_items)
            
            activity_breakdown.append({
                "activity_code": activity['code'],
                "activity_name": activity['name'],
                "component": activity['component'],
                "total_budget": total_cost,
                "percentage_of_total": 0,  # Will be calculated later
                "duration_months": activity['duration_months'],
                "cost_per_month": total_cost / activity['duration_months'],
                "budget_items_count": len(related_items),
                "complexity_level": activity.get('complexity', 'medium'),
                "geographic_scope": activity.get('geographic_scope', 'local')
            })
        
        # Calculate percentages
        total_project_budget = sum(ab['total_budget'] for ab in activity_breakdown)
        for ab in activity_breakdown:
            ab['percentage_of_total'] = (ab['total_budget'] / total_project_budget) * 100
        
        return activity_breakdown

    def _generate_equipment_budget(self, activities: List[Dict]) -> List[Dict]:
        """Generate equipment budget based on project needs"""
        equipment_items = []
        costs = self.guatemala_costs['equipment']
        
        # Standard equipment for development projects
        equipment_needs = [
            {
                "item": "Laptops para equipo técnico",
                "code": "E001",
                "unit_cost": costs['laptop_standard'],
                "quantity": 5,
                "useful_life_months": 36,
                "depreciation_project": 0.67,  # 24 months of 36 total
                "justification": "Equipos de cómputo para documentación, análisis y reportería"
            },
            {
                "item": "Tablets para trabajo de campo",
                "code": "E002", 
                "unit_cost": costs['tablet'],
                "quantity": 8,
                "useful_life_months": 24,
                "depreciation_project": 1.0,
                "justification": "Dispositivos móviles para recolección de datos en campo"
            },
            {
                "item": "Proyector portátil",
                "code": "E003",
                "unit_cost": costs['projector_portable'],
                "quantity": 2,
                "useful_life_months": 60,
                "depreciation_project": 0.40,
                "justification": "Equipos audiovisuales para capacitaciones y presentaciones"
            },
            {
                "item": "Vehículo pick-up usado",
                "code": "E004",
                "unit_cost": costs['vehicle_pickup_used'],
                "quantity": 1,
                "useful_life_months": 60,
                "depreciation_project": 0.40,
                "justification": "Transporte para supervisión y logística en comunidades rurales"
            }
        ]
        
        for equipment in equipment_needs:
            project_cost = equipment['unit_cost'] * equipment['quantity'] * equipment['depreciation_project']
            
            equipment_items.append({
                "item_code": equipment['code'],
                "activity_code": "ALL",
                "category": "Equipamiento, Suministros y Materiales",
                "subcategory": "Equipos de Oficina y Campo",
                "description": equipment['item'],
                "unit": "unidad",
                "quantity": equipment['quantity'],
                "unit_cost": equipment['unit_cost'] * equipment['depreciation_project'],
                "total_cost": project_cost,
                "procurement_method": "Licitación pública",
                "justification": equipment['justification'],
                "donor_eligible": True,
                "phase": "Inicio",
                "asset_details": {
                    "useful_life_months": equipment['useful_life_months'],
                    "depreciation_rate": equipment['depreciation_project'],
                    "maintenance_cost_annual": project_cost * 0.05
                }
            })
        
        return equipment_items
    
    def _generate_travel_budget(self, activities: List[Dict]) -> List[Dict]:
        """Generate comprehensive travel budget"""
        travel_items = []
        costs = self.guatemala_costs['travel']
        
        # Calculate travel needs based on project geography and activities
        project_locations = self._analyze_project_geography()
        travel_intensive_activities = [a for a in activities if a.get('travel_intensive', False)]
        
        # Monthly supervision visits
        supervision_days_month = len(project_locations) * 2  # 2 days per location monthly
        supervision_months = self.project.get('duration_months', 24)
        
        travel_components = [
            {
                "component": "Supervisión mensual de campo",
                "code": "T001",
                "days_total": supervision_days_month * supervision_months,
                "per_diem_rate": costs['per_diem_regional_center'],
                "accommodation_rate": costs['accommodation_regional'],
                "transport_km_total": supervision_days_month * supervision_months * 150,
                "justification": "Supervisión técnica y acompañamiento en comunidades"
            },
            {
                "component": "Talleres de capacitación",
                "code": "T002", 
                "days_total": 48,  # 4 talleres x 3 días x 4 ubicaciones
                "per_diem_rate": costs['per_diem_rural_area'],
                "accommodation_rate": costs['accommodation_rural'],
                "transport_km_total": 2400,
                "justification": "Facilitación de talleres en comunidades beneficiarias"
            },
            {
                "component": "Reuniones de coordinación",
                "code": "T003",
                "days_total": 24,  # Reuniones mensuales en capital
                "per_diem_rate": costs['per_diem_guatemala_city'],
                "accommodation_rate": costs['accommodation_capital'],
                "transport_km_total": 1200,
                "justification": "Coordinación con donante y socios estratégicos"
            }
        ]
        
        for component in travel_components:
            # Per diem costs
            travel_items.append({
                "item_code": f"{component['code']}_PD",
                "activity_code": "ALL",
                "category": "Viajes, Transporte y Logística",
                "subcategory": "Viáticos",
                "description": f"Viáticos - {component['component']}",
                "unit": "día",
                "quantity": component['days_total'],
                "unit_cost": component['per_diem_rate'],
                "total_cost": component['days_total'] * component['per_diem_rate'],
                "procurement_method": "Pago directo",
                "justification": component['justification'],
                "donor_eligible": True,
                "phase": "Implementación"
            })
            
            # Accommodation costs
            travel_items.append({
                "item_code": f"{component['code']}_ACC",
                "activity_code": "ALL",
                "category": "Viajes, Transporte y Logística", 
                "subcategory": "Hospedaje",
                "description": f"Hospedaje - {component['component']}",
                "unit": "noche",
                "quantity": component['days_total'],
                "unit_cost": component['accommodation_rate'],
                "total_cost": component['days_total'] * component['accommodation_rate'],
                "procurement_method": "Pago directo",
                "justification": component['justification'],
                "donor_eligible": True,
                "phase": "Implementación"
            })
            
            # Transportation costs
            travel_items.append({
                "item_code": f"{component['code']}_TRANS",
                "activity_code": "ALL",
                "category": "Viajes, Transporte y Logística",
                "subcategory": "Combustible y Mantenimiento",
                "description": f"Transporte - {component['component']}",
                "unit": "kilómetro",
                "quantity": component['transport_km_total'],
                "unit_cost": costs['transport_per_km'],
                "total_cost": component['transport_km_total'] * costs['transport_per_km'],
                "procurement_method": "Pago directo",
                "justification": component['justification'],
                "donor_eligible": True,
                "phase": "Implementación"
            })
        
        return travel_items
    
    def _generate_training_budget(self, activities: List[Dict]) -> List[Dict]:
        """Generate comprehensive training and events budget"""
        training_items = []
        
        # Training events based on project scope
        training_events = [
            {
                "event": "Talleres de Diagnóstico Participativo",
                "code": "C001",
                "sessions": 8,  # 2 por comunidad x 4 comunidades
                "participants_per_session": 25,
                "duration_days": 2,
                "materials_per_participant": 15,
                "facilitator_fee_day": 200,
                "venue_cost_day": 80,
                "refreshments_per_person_day": 8
            },
            {
                "event": "Capacitación en Liderazgo Comunitario",
                "code": "C002",
                "sessions": 4,
                "participants_per_session": 30,
                "duration_days": 3,
                "materials_per_participant": 25,
                "facilitator_fee_day": 250,
                "venue_cost_day": 100,
                "refreshments_per_person_day": 10
            },
            {
                "event": "Talleres de Formulación de Proyectos",
                "code": "C003",
                "sessions": 6,
                "participants_per_session": 20,
                "duration_days": 2,
                "materials_per_participant": 20,
                "facilitator_fee_day": 200,
                "venue_cost_day": 80,
                "refreshments_per_person_day": 8
            }
        ]
        
        for event in training_events:
            total_participants = event['sessions'] * event['participants_per_session']
            total_days = event['sessions'] * event['duration_days']
            
            # Facilitator fees
            training_items.append({
                "item_code": f"{event['code']}_FAC",
                "activity_code": "A2.1",  # Training activities
                "category": "Capacitación, Talleres y Eventos",
                "subcategory": "Honorarios Facilitación",
                "description": f"Facilitadores - {event['event']}",
                "unit": "día",
                "quantity": total_days,
                "unit_cost": event['facilitator_fee_day'],
                "total_cost": total_days * event['facilitator_fee_day'],
                "procurement_method": "Contratación por servicios",
                "justification": f"Facilitación técnica especializada para {event['event']}",
                "donor_eligible": True,
                "phase": "Implementación"
            })
            
            # Materials and supplies
            training_items.append({
                "item_code": f"{event['code']}_MAT",
                "activity_code": "A2.1",
                "category": "Capacitación, Talleres y Eventos",
                "subcategory": "Materiales Didácticos",
                "description": f"Materiales - {event['event']}",
                "unit": "participante",
                "quantity": total_participants,
                "unit_cost": event['materials_per_participant'],
                "total_cost": total_participants * event['materials_per_participant'],
                "procurement_method": "Compra directa",
                "justification": f"Materiales didácticos y suministros para {event['event']}",
                "donor_eligible": True,
                "phase": "Implementación"
            })
            
            # Venue and logistics
            training_items.append({
                "item_code": f"{event['code']}_VEN",
                "activity_code": "A2.1",
                "category": "Capacitación, Talleres y Eventos",
                "subcategory": "Logística y Venues",
                "description": f"Alquiler de salones - {event['event']}",
                "unit": "día",
                "quantity": total_days,
                "unit_cost": event['venue_cost_day'],
                "total_cost": total_days * event['venue_cost_day'],
                "procurement_method": "Alquiler",
                "justification": f"Espacios apropiados para desarrollo de {event['event']}",
                "donor_eligible": True,
                "phase": "Implementación"
            })
            
            # Refreshments
            refreshments_total = total_participants * event['duration_days'] * event['refreshments_per_person_day']
            training_items.append({
                "item_code": f"{event['code']}_REF",
                "activity_code": "A2.1",
                "category": "Capacitación, Talleres y Eventos",
                "subcategory": "Refrigerios",
                "description": f"Alimentación - {event['event']}",
                "unit": "persona-día",
                "quantity": total_participants * event['duration_days'],
                "unit_cost": event['refreshments_per_person_day'],
                "total_cost": refreshments_total,
                "procurement_method": "Catering",
                "justification": f"Alimentación para participantes en {event['event']}",
                "donor_eligible": True,
                "phase": "Implementación"
            })
        
        return training_items
    
    def _generate_services_budget(self, activities: List[Dict]) -> List[Dict]:
        """Generate services and operational costs budget"""
        services_items = []
        costs = self.guatemala_costs
        
        # Essential services for project operation
        services = [
            {
                "service": "Auditoría Externa Anual",
                "code": "S001",
                "frequency": "annual",
                "unit_cost": costs['services']['external_audit']['average'],
                "quantity": 2,  # Assuming 2-year project
                "justification": "Auditoría financiera externa requerida por donante"
            },
            {
                "service": "Servicios Legales",
                "code": "S002",
                "frequency": "as_needed",
                "unit_cost": costs['services']['legal_services_hourly'],
                "quantity": 40,  # 40 hours estimated
                "justification": "Asesoría legal para contratos y cumplimiento normativo"
            },
            {
                "service": "Traducción de Documentos",
                "code": "S003",
                "frequency": "as_needed", 
                "unit_cost": costs['services']['translation_per_page'],
                "quantity": 200,  # 200 pages estimated
                "justification": "Traducción de documentos técnicos español-inglés"
            },
            {
                "service": "Desarrollo Web y Comunicaciones",
                "code": "S004",
                "frequency": "one_time",
                "unit_cost": costs['services']['web_design']['average'],
                "quantity": 1,
                "justification": "Desarrollo de plataforma web para visibilidad del proyecto"
            }
        ]
        
        for service in services:
            services_items.append({
                "item_code": service['code'],
                "activity_code": "ALL",
                "category": "Gastos Operativos y Servicios",
                "subcategory": "Servicios Profesionales",
                "description": service['service'],
                "unit": "servicio" if service['frequency'] == "one_time" else "hora" if "hourly" in service['code'] else "página" if "translation" in service['service'].lower() else "unidad",
                "quantity": service['quantity'],
                "unit_cost": service['unit_cost'],
                "total_cost": service['quantity'] * service['unit_cost'],
                "procurement_method": "Licitación por servicios",
                "justification": service['justification'],
                "donor_eligible": True,
                "phase": "Implementación"
            })
        
        # Monthly operational costs
        monthly_operations = [
            {
                "item": "Alquiler de oficina",
                "code": "O001",
                "monthly_cost": costs['operational']['office_rent_regional']['average'],
                "months": self.project.get('duration_months', 24)
            },
            {
                "item": "Servicios de Internet y Comunicaciones",
                "code": "O002",
                "monthly_cost": costs['operational']['internet_office'] + costs['operational']['telephone_mobile'] * 5,
                "months": self.project.get('duration_months', 24)
            },
            {
                "item": "Servicios Básicos (Electricidad y Agua)",
                "code": "O003",
                "monthly_cost": costs['operational']['electricity_monthly']['average'] + costs['operational']['water_monthly']['average'],
                "months": self.project.get('duration_months', 24)
            },
            {
                "item": "Suministros de Oficina",
                "code": "O004",
                "monthly_cost": costs['operational']['office_supplies_monthly'],
                "months": self.project.get('duration_months', 24)
            },
            {
                "item": "Mantenimiento de Vehículos",
                "code": "O005",
                "monthly_cost": costs['operational']['vehicle_maintenance_monthly'],
                "months": self.project.get('duration_months', 24)
            }
        ]
        
        for operation in monthly_operations:
            services_items.append({
                "item_code": operation['code'],
                "activity_code": "ALL",
                "category": "Gastos Operativos y Servicios",
                "subcategory": "Gastos de Funcionamiento",
                "description": operation['item'],
                "unit": "mes",
                "quantity": operation['months'],
                "unit_cost": operation['monthly_cost'],
                "total_cost": operation['months'] * operation['monthly_cost'],
                "procurement_method": "Pago directo",
                "justification": f"Gastos operativos mensuales necesarios - {operation['item']}",
                "donor_eligible": True,
                "phase": "Implementación"
            })
        
        return services_items
    
    def _analyze_project_geography(self) -> List[str]:
        """Analyze project geographical scope"""
        coverage = self.project.get('coverage_type', 'Local')
        department = self.project.get('department', '')
        municipality = self.project.get('municipality', '')
        
        if coverage == 'Nacional':
            return ['Guatemala City', 'Quetzaltenango', 'Cobán', 'Puerto Barrios']
        elif coverage == 'Departamental':
            return [department, f"{department}_rural"]
        elif coverage == 'Municipal':
            return [municipality] if municipality else ['Location_1']
        else:
            return [municipality or 'Community_1', 'Community_2']
    
    def _generate_category_breakdown(self, budget_items: List[Dict]) -> Dict:
        """Generate detailed breakdown by budget category"""
        category_breakdown = {}
        
        for item in budget_items:
            category = item['category']
            if category not in category_breakdown:
                category_breakdown[category] = {
                    'total_amount': 0,
                    'item_count': 0,
                    'percentage': 0,
                    'subcategories': {}
                }
            
            category_breakdown[category]['total_amount'] += item['total_cost']
            category_breakdown[category]['item_count'] += 1
            
            subcategory = item.get('subcategory', 'General')
            if subcategory not in category_breakdown[category]['subcategories']:
                category_breakdown[category]['subcategories'][subcategory] = 0
            category_breakdown[category]['subcategories'][subcategory] += item['total_cost']
        
        # Calculate percentages
        total_budget = sum(cat['total_amount'] for cat in category_breakdown.values())
        for category_data in category_breakdown.values():
            category_data['percentage'] = (category_data['total_amount'] / total_budget) * 100
        
        return category_breakdown
    
    def _generate_timeline_breakdown(self, activities: List[Dict], budget_items: List[Dict]) -> Dict:
        """Generate monthly cash flow projection"""
        duration_months = self.project.get('duration_months', 24)
        monthly_breakdown = {f"Month_{i+1}": 0 for i in range(duration_months)}
        
        # Distribute costs across project timeline based on activities
        for item in budget_items:
            if item.get('activity_code') == 'ALL':
                # Distribute evenly across all months
                monthly_cost = item['total_cost'] / duration_months
                for month in monthly_breakdown:
                    monthly_breakdown[month] += monthly_cost
            else:
                # Find corresponding activity and distribute across its duration
                activity = next((a for a in activities if a['code'] == item['activity_code']), None)
                if activity:
                    start_month = activity['start_month']
                    end_month = activity['end_month']
                    months_span = end_month - start_month + 1
                    monthly_cost = item['total_cost'] / months_span
                    
                    for i in range(start_month - 1, end_month):
                        if i < len(monthly_breakdown):
                            month_key = f"Month_{i+1}"
                            monthly_breakdown[month_key] += monthly_cost
        
        # Generate quarterly breakdown
        quarterly_breakdown = {}
        for i in range(0, duration_months, 3):
            quarter = f"Q{(i//3)+1}"
            quarter_total = sum(monthly_breakdown[f"Month_{j+1}"] 
                              for j in range(i, min(i+3, duration_months)))
            quarterly_breakdown[quarter] = quarter_total
        
        return {
            "monthly_distribution": monthly_breakdown,
            "quarterly_distribution": quarterly_breakdown,
            "cash_flow_projection": self._generate_cash_flow_projection(monthly_breakdown)
        }
    
    def _generate_cash_flow_projection(self, monthly_breakdown: Dict) -> Dict:
        """Generate cumulative cash flow projection"""
        months = sorted(monthly_breakdown.keys(), key=lambda x: int(x.split('_')[1]))
        cumulative = 0
        cash_flow = {}
        
        for month in months:
            cumulative += monthly_breakdown[month]
            cash_flow[month] = {
                "monthly_expense": monthly_breakdown[month],
                "cumulative_expense": cumulative,
                "percentage_executed": (cumulative / sum(monthly_breakdown.values())) * 100
            }
        
        return cash_flow
    
    def _validate_donor_compliance(self, budget_items: List[Dict], standards: Dict) -> Dict:
        """Validate budget compliance with donor standards"""
        total_budget = sum(item['total_cost'] for item in budget_items)
        
        # Calculate indirect cost rate
        direct_costs = sum(item['total_cost'] for item in budget_items 
                          if item['category'] != 'Costos Administrativos')
        indirect_costs = total_budget - direct_costs
        actual_indirect_rate = indirect_costs / direct_costs if direct_costs > 0 else 0
        
        compliance_issues = []
        if actual_indirect_rate > standards['indirect_cost_rate']:
            compliance_issues.append(f"Indirect cost rate {actual_indirect_rate:.1%} exceeds donor limit of {standards['indirect_cost_rate']:.1%}")
        
        # Check required categories
        budget_categories = set(item['category'] for item in budget_items)
        required_categories = set(standards.get('required_categories', []))
        missing_categories = required_categories - budget_categories
        
        if missing_categories:
            compliance_issues.append(f"Missing required budget categories: {', '.join(missing_categories)}")
        
        return {
            "compliant": len(compliance_issues) == 0,
            "issues": compliance_issues,
            "indirect_cost_rate": actual_indirect_rate,
            "donor_limit": standards['indirect_cost_rate'],
            "audit_requirements": standards.get('audit_requirements', 'Not specified')
        }
    
    def _validate_guatemala_compliance(self, budget_items: List[Dict]) -> Dict:
        """Validate compliance with Guatemala regulations"""
        compliance_items = []
        
        # Check for required tax considerations
        personnel_items = [item for item in budget_items if 'Personal' in item['category']]
        if personnel_items:
            compliance_items.append({
                "regulation": "Código de Trabajo de Guatemala",
                "requirement": "Prestaciones laborales según ley",
                "status": "Included",
                "note": "Prestaciones calculadas al 41.83% del salario base"
            })
        
        # Check for IVA considerations
        equipment_items = [item for item in budget_items if 'Equipamiento' in item['category']]
        if equipment_items:
            compliance_items.append({
                "regulation": "Ley del IVA (Decreto 27-92)",
                "requirement": "IVA 12% en compra de bienes",
                "status": "To be applied",
                "note": "IVA debe ser calculado en fase de adquisiciones"
            })
        
        return {
            "regulatory_framework": "Guatemala Legal Framework",
            "compliance_items": compliance_items,
            "tax_considerations": {
                "iva_rate": 0.12,
                "isr_applicable": True,
                "social_security_rate": 0.1267
            }
        }
    
    def _generate_budget_kpis(self, total_budget: float) -> List[Dict]:
        """Generate budget performance indicators"""
        return [
            {
                "indicator": "Ratio Costos Directos/Indirectos",
                "target": "≥ 90% costos directos",
                "measurement": "Porcentaje del presupuesto en actividades directas",
                "frequency": "Trimestral"
            },
            {
                "indicator": "Costo por Beneficiario Directo", 
                "target": f"≤ ${total_budget / max(self._parse_beneficiaries(self.project.get('beneficiaries_direct', '100')), 1):,.0f}",
                "measurement": "Presupuesto total / beneficiarios directos",
                "frequency": "Anual"
            },
            {
                "indicator": "Eficiencia de Ejecución Presupuestal",
                "target": "≥ 95% de ejecución anual",
                "measurement": "Porcentaje del presupuesto ejecutado vs planificado",
                "frequency": "Mensual"
            },
            {
                "indicator": "Cumplimiento de Cronograma Financiero",
                "target": "± 5% de desviación",
                "measurement": "Comparación gasto real vs proyectado mensual",
                "frequency": "Mensual"
            }
        ]
    
    def _assess_cost_effectiveness(self, total_budget: float, beneficiaries: int) -> str:
        """Assess cost effectiveness rating"""
        if beneficiaries == 0:
            return "No determinado"
        
        cost_per_beneficiary = total_budget / beneficiaries
        
        # Benchmarks for development projects in Guatemala
        if cost_per_beneficiary <= 200:
            return "Excelente"
        elif cost_per_beneficiary <= 400:
            return "Muy bueno"
        elif cost_per_beneficiary <= 600:
            return "Bueno"
        elif cost_per_beneficiary <= 1000:
            return "Aceptable"
        else:
            return "Requiere justificación"