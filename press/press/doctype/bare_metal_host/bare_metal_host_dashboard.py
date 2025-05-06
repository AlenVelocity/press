from frappe import _

def get_data():
	return {
		'fieldname': 'host',
		'non_standard_fieldnames': {
			'Virtual Machine': 'parent_host',
			'Server': 'bare_metal_host'
		},
		'transactions': [
			{
				'label': _('Resources'),
				'items': ['Resource Allocation']
			},
			{
				'label': _('Related Documents'),
				'items': ['Virtual Machine', 'Server']
			}
		],
		'charts': [
			{
				'chart_name': 'Resource Utilization',
				'chart_type': 'Percentage',
				'filters_json': '{}',
				'doctype': 'Bare Metal Host',
				'source': 'Resource Utilization',
				'document_name': ''
			}
		]
	} 