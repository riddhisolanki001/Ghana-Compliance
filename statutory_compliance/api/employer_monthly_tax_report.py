import frappe
import calendar
from erpnext import get_default_company
from datetime import datetime
from frappe.utils import get_first_day, get_last_day, nowdate
from collections import defaultdict

@frappe.whitelist()
def get_data_employer_monthly_tax_report(month=None, year=None):
    data = {}
    data["employee"] = []
    totals = defaultdict(float)
    company_name = get_default_company()

    if not company_name:
        company_name = frappe.db.get_value("Company", {"is_group": 0}, "name")

    company = frappe.get_doc("Company", company_name)
    
    if not month or not year:
        current_date = nowdate()
        dt = datetime.strptime(current_date, "%Y-%m-%d")
        month = dt.month
        year = dt.year
    else:
        # Ensure integers
        month = int(month)
        year = int(year)
        dt = datetime(year, month, 1)

    data["date"] = dt.strftime("%m/%Y")
    data['custom_tax_office'] = company.custom_tax_office
    data["company_name"] = company.name
    data["company_custom_tngh_card_number"] = company.custom_tngh_card_number

    employees = frappe.get_all("Employee")
    month_start = f"{year}-{str(month).zfill(2)}-01"
    month_end = f"{year}-{str(month).zfill(2)}-{calendar.monthrange(year, month)[1]}"

    for emp in employees:
        employee_doc = frappe.get_doc("Employee", emp["name"])

        salary_structure = frappe.get_all(
            "Salary Structure Assignment",
            filters={"employee": employee_doc.name, "docstatus": 1},
            fields=["name", "base", "from_date", "income_tax_slab"],
            order_by="from_date desc",
            limit=1
        )
        
        basic_salary = salary_structure[0].base if salary_structure else 0
        income_tax_slab = salary_structure[0].income_tax_slab if salary_structure and salary_structure[0].income_tax_slab else None

        ssf_percent = company.custom_social_security_fund or 0
        third_tier_percent = employee_doc.custom_third_tier_percentage or 0

        salary_slip = frappe.get_all(
            "Salary Slip",
            filters={
                "employee": employee_doc.name,
                "start_date": ["<=", month_start],
                "end_date": [">=", month_end],
                "docstatus": 1
            },
            fields=["name"],
            order_by="end_date desc",
            limit=1
        )

        cash_allowance_total = 0
        if salary_slip:
            slip_doc = frappe.get_doc("Salary Slip", salary_slip[0].name)
            for earning in slip_doc.earnings:
                salary_component = frappe.get_doc("Salary Component", earning.salary_component)
                if salary_component.custom_is_cash_allowance:
                    cash_allowance_total += earning.amount
        
        social_security_fund = (basic_salary * ssf_percent) / 100
        third_tier = (basic_salary * third_tier_percent) / 100
        total_cash_emolument = basic_salary + cash_allowance_total
        total_assessable_income = total_cash_emolument + employee_doc.custom_accommodation_element + employee_doc.custom_vehicle_element + employee_doc.custom_non_cash_benefit
        total_reliefs = social_security_fund + third_tier + employee_doc.custom_deductible_reliefs
        chargeable_income = total_assessable_income - total_reliefs

        tax_deductible = 0.0
        if income_tax_slab:
            slab_doc = frappe.get_doc("Income Tax Slab", income_tax_slab)
            for slab in slab_doc.slabs:
                from_amt = slab.from_amount or 0
                to_amt = slab.to_amount or 0
                percent = slab.percent_deduction or 0
                if from_amt <= chargeable_income <= to_amt:
                    tax_deductible = (chargeable_income * percent) / 100
                    break
        
        final_tax_bonus = 0.00
        overtime_income = 0.00
        overtime_tax = 0.00
        total_tax_payable_to_gra = final_tax_bonus + tax_deductible + overtime_tax
        severance_pay_paid = employee_doc.custom_severance_pay_paid

        totals["total_cash_emolument"] += total_cash_emolument
        totals["custom_accommodation_element"] += employee_doc.custom_accommodation_element
        totals["custom_vehicle_element"] += employee_doc.custom_vehicle_element
        totals["custom_non_cash_benefit"] += employee_doc.custom_non_cash_benefit
        totals["total_assessable_income"] += total_assessable_income
        totals["custom_deductible_reliefs"] += employee_doc.custom_deductible_reliefs
        totals["total_reliefs"] += total_reliefs
        totals["chargeable_income"] += chargeable_income
        totals["tax_deductible"] += tax_deductible
        totals["overtime_income"] += overtime_income
        totals["overtime_tax"] += overtime_tax
        totals["total_tax_payable_to_gra"] += total_tax_payable_to_gra
        totals["severance_pay_paid"] += severance_pay_paid
        
        data["employee"].append({
            "custom_tingh_card_number": employee_doc.custom_tingh_card_number,
            "employee_name": employee_doc.employee_name,
            "position": employee_doc.designation,
            "employment_type": employee_doc.employment_type,
            "basic_salary": format(basic_salary, ".2f"),
            "custom_secondary_employment": employee_doc.custom_secondary_employment,
            "custom_allow_to_contribute": employee_doc.custom_allow_to_contribute,
            "social_security_fund": format(social_security_fund, ".2f"),
            "third_tier": format(third_tier, ".2f"),
            "cash_allowances": format(cash_allowance_total, ".2f"),
            "bonus_income": "0.00",
            "final_tax_bonus": format(final_tax_bonus, ".2f"),
            "excess_bonus": "0.00",
            "total_cash_emolument": format(total_cash_emolument, ".2f"),
            "custom_accommodation_element": format(employee_doc.custom_accommodation_element, ".2f"),
            "custom_vehicle_element": format(employee_doc.custom_vehicle_element, ".2f"),
            "custom_non_cash_benefit": format(employee_doc.custom_non_cash_benefit, ".2f"),
            "total_assessable_income": format(total_assessable_income, ".2f"),
            "custom_deductible_reliefs": format(employee_doc.custom_deductible_reliefs, ".2f"),
            "total_reliefs": format(total_reliefs, ".2f"),
            "chargeable_income": format(chargeable_income, ".2f"),
            "tax_deductible": format(tax_deductible, ".2f"),
            "overtime_income": format(overtime_income, ".2f"),
            "overtime_tax": format(overtime_tax, ".2f"),
            "total_tax_payable_to_gra": format(total_tax_payable_to_gra, ".2f"),
            "severance_pay_paid": format(severance_pay_paid, ".2f")
        })
    
    data["totals"] = {key: format(value, ".2f") for key, value in totals.items()}
    return data
