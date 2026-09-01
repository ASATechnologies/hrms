# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class EmployeeSalaryVariables(Document):
    def validate(self):
        self.validate_duplicate_components()
        self.validate_component_variables()
        self.validate_components_in_salary_structure()
        self.validate_only_variable_components()

    def validate_components_in_salary_structure(self):
        """
        Ensure all salary components exist in the selected salary structure.
        """
        if not self.salary_structure:
            frappe.throw(_("Please select a Salary Structure"))

        # Get all components from the salary structure
        structure_components = frappe.get_all(
            "Salary Detail",
            filters={
                "parent": self.salary_structure,
                "parentfield": ["in", ["earnings", "deductions"]],
            },
            fields=["salary_component"],
        )

        valid_components = {sc.salary_component for sc in structure_components}

        for row in self.component_variables:
            if row.salary_component not in valid_components:
                frappe.throw(
                    _(
                        "Row {0}: Salary Component {1} does not exist in Salary Structure {2}"
                    ).format(
                        row.idx,
                        frappe.bold(row.salary_component),
                        frappe.bold(self.salary_structure),
                    )
                )

    def validate_only_variable_components(self):
        """
        Ensure all components are marked as employee variable in the Salary Structure.
        Note: amount_based_on_employee_variable is now in Salary Detail, not Salary Component.
        """
        if not self.salary_structure:
            return

        for row in self.component_variables:
            # Check if this component has amount_based_on_employee_variable enabled
            # in the Salary Detail of the selected Salary Structure
            is_variable = frappe.db.get_value(
                "Salary Detail",
                {
                    "parent": self.salary_structure,
                    "salary_component": row.salary_component,
                    "parentfield": ["in", ["earnings", "deductions"]],
                },
                "amount_based_on_employee_variable",
            )

            if not is_variable:
                frappe.throw(
                    _(
                        "Row {0}: Salary Component {1} is not configured as an employee variable component in Salary Structure {2}"
                    ).format(
                        row.idx,
                        frappe.bold(row.salary_component),
                        frappe.bold(self.salary_structure),
                    )
                )

    def validate_duplicate_components(self):
        """
        Prevent duplicate (salary_component, project, activity) combinations.
        For fixed_amount: only salary_component matters
        For project: (salary_component, project, activity) must be unique
        """
        seen = set()

        for row in self.component_variables:
            if row.derived_from == "fixed_amount":
                # For fixed amount, just check salary component
                key = (row.salary_component, None, None)
                error_msg = _("Row {0}: Duplicate salary component {1}").format(
                    row.idx, frappe.bold(row.salary_component)
                )
            else:  # project
                # For project-based, check (salary_component, project, activity)
                key = (row.salary_component, row.project, row.activity)
                error_msg = _("Row {0}: Duplicate entry for {1} - {2} - {3}").format(
                    row.idx,
                    frappe.bold(row.salary_component),
                    frappe.bold(row.project),
                    frappe.bold(row.activity),
                )

            if key in seen:
                frappe.throw(error_msg)
            seen.add(key)

    def validate_component_variables(self):
        """Validate derived_from logic"""
        for row in self.component_variables:
            if row.derived_from == "fixed_amount":
                if not row.amount:
                    frappe.throw(
                        _(
                            "Row {0}: Amount is required when Derived From is 'Fixed Amount'"
                        ).format(row.idx)
                    )
                if row.project or row.activity or row.hourly_rate:
                    frappe.throw(
                        _(
                            "Row {0}: Project, Activity and Hourly Rate should be empty for 'Fixed Amount'"
                        ).format(row.idx)
                    )

            elif row.derived_from == "project":
                if not row.project or not row.activity or not row.hourly_rate:
                    frappe.throw(
                        _(
                            "Row {0}: Project, Activity and Hourly Rate are required when Derived From is 'Project'"
                        ).format(row.idx)
                    )
                if row.amount:
                    frappe.throw(
                        _(
                            "Row {0}: Amount should be empty for 'Project' based components"
                        ).format(row.idx)
                    )


# employee_salary_variable.py


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_variable_salary_components(doctype, txt, searchfield, start, page_len, filters):
    """
    Custom query to fetch only salary components that are marked as
    employee variable in the given salary structure.
    """
    salary_structure = filters.get("salary_structure")

    if not salary_structure:
        return []

    return frappe.db.sql(
        """
        SELECT DISTINCT sd.salary_component, sc.salary_component_abbr
        FROM `tabSalary Detail` sd
        INNER JOIN `tabSalary Component` sc ON sd.salary_component = sc.name
        WHERE sd.parent = %(salary_structure)s
            AND sd.parentfield IN ('earnings', 'deductions')
            AND sd.amount_based_on_employee_variable = 1
            AND (sd.salary_component LIKE %(txt)s OR sc.salary_component_abbr LIKE %(txt)s)
        ORDER BY sd.salary_component
        LIMIT %(start)s, %(page_len)s
    """,
        {
            "salary_structure": salary_structure,
            "txt": f"%{txt}%",
            "start": start,
            "page_len": page_len,
        },
    )
