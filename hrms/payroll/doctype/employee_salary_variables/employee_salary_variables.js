// Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Employee Salary Variables", {
	refresh: function (frm) {
		// Set filter for employee based on salary structure if needed
		if (frm.doc.salary_structure) {
			frm.set_query("employee", function () {
				return {
					filters: {
						status: "Active",
					},
				};
			});
		}
	},
});

frappe.ui.form.on("Employee Salary Variables Detail", {
	component_variables_add: function (frm, cdt, cdn) {
		// Set query filter for salary_component
		let row = locals[cdt][cdn];

		if (frm.doc.salary_structure) {
			frm.fields_dict["component_variables"].grid.update_docfield_property(
				"salary_component",
				"get_query",
				function () {
					return {
						query: "hrms.payroll.doctype.employee_salary_variables.employee_salary_variables.get_variable_salary_components",
						filters: {
							salary_structure: frm.doc.salary_structure,
						},
					};
				}
			);
		}
	},

	derived_from: function (frm, cdt, cdn) {
		let row = locals[cdt][cdn];

		// Clear fields based on derived_from selection
		if (row.derived_from === "Fixed Amount") {
			frappe.model.set_value(cdt, cdn, "project", "");
			frappe.model.set_value(cdt, cdn, "activity", "");
			frappe.model.set_value(cdt, cdn, "hourly_rate", 0);
		} else if (row.derived_from === "Project Timesheet") {
			frappe.model.set_value(cdt, cdn, "amount", 0);
		}
	},
});
