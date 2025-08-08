frappe.pages['employer-monthly-tax'].on_page_load = function(wrapper) {
	let page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Employer Monthly Tax',
		single_column: true
	});

	enableFullsizeView();
	$(window).on('beforeunload', () => revertToNormalView());

	function enableFullsizeView() {
		document.body.classList.add("full-width");
	}
	function revertToNormalView() {
		document.body.classList.remove("full-width");
	}

	const currentMonth = moment().month() + 1; // moment month is 0-indexed
	const currentYear = moment().year();

	// Render filter UI
	$(`
		<div class="form-inline" style="margin-bottom: 15px;">
			<label style="margin-right: 10px;">Select Month:</label>
			<select id="select-month" class="form-control" style="margin-right: 20px;">
				${[...Array(12)].map((_, i) => {
					const monthNum = i + 1;
					const monthName = moment().month(i).format("MMMM");
					const selected = monthNum === currentMonth ? "selected" : "";
					return `<option value="${monthNum}" ${selected}>${monthName}</option>`;
				}).join('')}
			</select>

			<label style="margin-right: 10px;">Select Year:</label>
			<select id="select-year" class="form-control" style="margin-right: 20px;">
				${[...Array(10)].map((_, i) => {
					const year = currentYear - i;
					const selected = year === currentYear ? "selected" : "";
					return `<option value="${year}" ${selected}>${year}</option>`;
				}).join('')}
			</select>

			<button id="generate-tax-report" class="btn btn-primary">Generate</button>
		</div>
	`).appendTo(page.body);

	// Click event
	$('#generate-tax-report').on('click', function () {
		const month = $('#select-month').val();
		const year = $('#select-year').val();

		frappe.call({
			method: "statutory_compliance.api.employer_monthly_tax_report.get_data_employer_monthly_tax_report",
			args: { month, year },
			callback: function (r) {
				const data = r.message;
				console.log(data);

				// Remove existing table before appending new one
				$(".table-container").remove();

				// Append updated template
				$(frappe.render_template("employer_monthly_tax_template", { data })).appendTo(page.body);
			}
		});
	});
	$('#generate-tax-report').click();
};