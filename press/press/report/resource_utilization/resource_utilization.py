# Copyright (c) 2025, Frappe and contributors
# For license information, please see license.txt

import frappe
from frappe import _

def execute(filters=None):
	if not filters:
		filters = {}
		
	columns = get_columns()
	data = get_data(filters)
	
	chart = get_chart_data(data)
	
	return columns, data, None, chart

def get_columns():
	return [
		{
			"fieldname": "host",
			"label": _("Host"),
			"fieldtype": "Link",
			"options": "Bare Metal Host",
			"width": 180
		},
		{
			"fieldname": "hostname",
			"label": _("Hostname"),
			"fieldtype": "Data",
			"width": 180
		},
		{
			"fieldname": "ip",
			"label": _("IP Address"),
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "total_cpu",
			"label": _("Total CPU"),
			"fieldtype": "Float",
			"width": 100
		},
		{
			"fieldname": "allocated_cpu",
			"label": _("Used CPU"),
			"fieldtype": "Float",
			"width": 100
		},
		{
			"fieldname": "cpu_percent",
			"label": _("CPU %"),
			"fieldtype": "Percent",
			"width": 80
		},
		{
			"fieldname": "total_memory",
			"label": _("Total Memory (MB)"),
			"fieldtype": "Float",
			"width": 150
		},
		{
			"fieldname": "allocated_memory",
			"label": _("Used Memory (MB)"),
			"fieldtype": "Float",
			"width": 150
		},
		{
			"fieldname": "memory_percent",
			"label": _("Memory %"),
			"fieldtype": "Percent",
			"width": 80
		},
		{
			"fieldname": "total_disk",
			"label": _("Total Disk (GB)"),
			"fieldtype": "Float",
			"width": 120
		},
		{
			"fieldname": "allocated_disk",
			"label": _("Used Disk (GB)"),
			"fieldtype": "Float",
			"width": 120
		},
		{
			"fieldname": "disk_percent",
			"label": _("Disk %"),
			"fieldtype": "Percent",
			"width": 80
		}
	]

def get_data(filters):
	conditions = ""
	
	if filters.get("host"):
		conditions += f" AND bm.name = '{filters.get('host')}'"
		
	if filters.get("status"):
		conditions += f" AND bm.status = '{filters.get('status')}'"
		
	if filters.get("region"):
		conditions += f" AND bm.region = '{filters.get('region')}'"
		
	data = frappe.db.sql(f"""
		SELECT 
			bm.name as host,
			bm.hostname,
			bm.ip,
			IFNULL(bm.total_cpu, 0) as total_cpu,
			IFNULL(bm.allocated_cpu, 0) as allocated_cpu,
			CASE WHEN IFNULL(bm.total_cpu, 0) > 0 
				THEN (IFNULL(bm.allocated_cpu, 0) / IFNULL(bm.total_cpu, 1)) * 100
				ELSE 0
			END as cpu_percent,
			IFNULL(bm.total_memory, 0) as total_memory,
			IFNULL(bm.allocated_memory, 0) as allocated_memory,
			CASE WHEN IFNULL(bm.total_memory, 0) > 0 
				THEN (IFNULL(bm.allocated_memory, 0) / IFNULL(bm.total_memory, 1)) * 100
				ELSE 0
			END as memory_percent,
			IFNULL(bm.total_disk, 0) as total_disk,
			IFNULL(bm.allocated_disk, 0) as allocated_disk,
			CASE WHEN IFNULL(bm.total_disk, 0) > 0 
				THEN (IFNULL(bm.allocated_disk, 0) / IFNULL(bm.total_disk, 1)) * 100
				ELSE 0
			END as disk_percent
		FROM 
			`tabBare Metal Host` bm
		WHERE 
			bm.docstatus < 2
			{conditions}
		ORDER BY 
			bm.hostname
	""", as_dict=1)
	
	return data

def get_chart_data(data):
	if not data:
		return None
		
	labels = []
	cpu_data = []
	memory_data = []
	disk_data = []
	
	for row in data:
		labels.append(row.hostname or row.host)
		cpu_data.append(row.cpu_percent)
		memory_data.append(row.memory_percent)
		disk_data.append(row.disk_percent)
		
	return {
		"data": {
			"labels": labels,
			"datasets": [
				{"name": "CPU Usage (%)", "values": cpu_data},
				{"name": "Memory Usage (%)", "values": memory_data},
				{"name": "Disk Usage (%)", "values": disk_data}
			]
		},
		"type": "bar",
		"colors": ["#7cd6fd", "#743ee2", "#5e64ff"],
		"axisOptions": {
			"xIsSeries": 1
		}
	} 