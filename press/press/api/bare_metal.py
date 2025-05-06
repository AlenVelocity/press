# Copyright (c) 2025, Frappe and contributors
# For license information, please see license.txt

import frappe
import json
from frappe import _
from frappe.utils import cint, flt

@frappe.whitelist()
def get_hosts(filters=None, fields=None):
	"""Get bare metal hosts with filters"""
	if isinstance(filters, str):
		filters = json.loads(filters)
		
	if isinstance(fields, str):
		fields = json.loads(fields)
		
	# Default fields if not specified
	if not fields:
		fields = [
			"name", "hostname", "ip", "status", "region", 
			"total_cpu", "available_cpu", "total_memory", 
			"available_memory", "total_disk", "available_disk"
		]
		
	hosts = frappe.get_all(
		"Bare Metal Host",
		filters=filters,
		fields=fields
	)
	
	return hosts

@frappe.whitelist()
def get_host_details(host_name):
	"""Get detailed information about a specific host"""
	if not frappe.has_permission("Bare Metal Host", "read"):
		frappe.throw(_("Not permitted"), frappe.PermissionError)
		
	host = frappe.get_doc("Bare Metal Host", host_name)
	
	# Get resource allocations
	allocations = frappe.get_all(
		"Resource Allocation",
		filters={"host": host_name},
		fields=[
			"name", "purpose", "allocated_cpu", "allocated_memory", 
			"allocated_disk", "allocation_date", "reference_type", 
			"reference_name"
		]
	)
	
	# Calculate usage percentages
	cpu_usage = (host.allocated_cpu / host.total_cpu * 100) if host.total_cpu else 0
	memory_usage = (host.allocated_memory / host.total_memory * 100) if host.total_memory else 0
	disk_usage = (host.allocated_disk / host.total_disk * 100) if host.total_disk else 0
	
	return {
		"host": host.as_dict(),
		"allocations": allocations,
		"usage": {
			"cpu_percent": round(cpu_usage, 2),
			"memory_percent": round(memory_usage, 2),
			"disk_percent": round(disk_usage, 2)
		}
	}

@frappe.whitelist()
def provision_host(host_name):
	"""Provision the specified host"""
	if not frappe.has_permission("Bare Metal Host", "write"):
		frappe.throw(_("Not permitted"), frappe.PermissionError)
		
	host = frappe.get_doc("Bare Metal Host", host_name)
	result = host.provision_host()
	
	return result

@frappe.whitelist()
def setup_vm_host(host_name):
	"""Set up host as VM host"""
	if not frappe.has_permission("Bare Metal Host", "write"):
		frappe.throw(_("Not permitted"), frappe.PermissionError)
		
	host = frappe.get_doc("Bare Metal Host", host_name)
	result = host.setup_vm_host()
	
	return result

@frappe.whitelist()
def allocate_resources(host_name, purpose, cpu=0, memory_mb=0, disk_gb=0, allocation_reference=None):
	"""Allocate resources on the host"""
	if not frappe.has_permission("Bare Metal Host", "write"):
		frappe.throw(_("Not permitted"), frappe.PermissionError)
		
	host = frappe.get_doc("Bare Metal Host", host_name)
	
	result = host.allocate_resources(
		purpose=purpose,
		cpu=flt(cpu),
		memory_mb=flt(memory_mb),
		disk_gb=flt(disk_gb),
		allocation_reference=allocation_reference
	)
	
	return result

@frappe.whitelist()
def deallocate_resources(host_name, allocation_id):
	"""Deallocate resources from the host"""
	if not frappe.has_permission("Bare Metal Host", "write"):
		frappe.throw(_("Not permitted"), frappe.PermissionError)
		
	host = frappe.get_doc("Bare Metal Host", host_name)
	result = host.deallocate_resources(allocation_id)
	
	return result

@frappe.whitelist()
def setup_monitoring(host_name, monitoring_type="prometheus", metrics_port=9100, monitoring_token=None):
	"""Set up monitoring on the host"""
	if not frappe.has_permission("Bare Metal Host", "write"):
		frappe.throw(_("Not permitted"), frappe.PermissionError)
		
	host = frappe.get_doc("Bare Metal Host", host_name)
	
	result = host.setup_monitoring(
		monitoring_type=monitoring_type,
		metrics_port=cint(metrics_port),
		monitoring_token=monitoring_token
	)
	
	return result

@frappe.whitelist()
def setup_backup(host_name, backup_schedule="0 2 * * *", backup_retention=7, backup_destination=None):
	"""Set up backup on the host"""
	if not frappe.has_permission("Bare Metal Host", "write"):
		frappe.throw(_("Not permitted"), frappe.PermissionError)
		
	host = frappe.get_doc("Bare Metal Host", host_name)
	
	result = host.setup_backup(
		backup_schedule=backup_schedule,
		backup_retention=cint(backup_retention),
		backup_destination=backup_destination
	)
	
	return result 