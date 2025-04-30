# Copyright (c) 2025, Frappe and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class ResourceAllocation(Document):
	def validate(self):
		self.validate_allocation()
		
	def validate_allocation(self):
		"""Validate allocation values are positive and host exists"""
		if self.allocated_cpu < 0:
			frappe.throw("Allocated CPU cannot be negative")
			
		if self.allocated_memory < 0:
			frappe.throw("Allocated memory cannot be negative")
			
		if self.allocated_disk < 0:
			frappe.throw("Allocated disk space cannot be negative")
			
		if not frappe.db.exists("Bare Metal Host", self.host):
			frappe.throw(f"Host {self.host} does not exist")
	
	def on_trash(self):
		"""Handle resource deallocation on delete if not called from deallocate_resources"""
		if hasattr(self, '_skip_resource_update'):
			return
			
		host = frappe.get_doc("Bare Metal Host", self.host)
		
		# Update available resources
		host.available_cpu = host.available_cpu + self.allocated_cpu
		host.available_memory = host.available_memory + self.allocated_memory
		host.available_disk = host.available_disk + self.allocated_disk
		
		# Update allocation counts
		host.total_allocations = frappe.db.count("Resource Allocation", {"host": host.name})
		host.allocated_cpu = host.total_cpu - host.available_cpu
		host.allocated_memory = host.total_memory - host.available_memory
		host.allocated_disk = host.total_disk - host.available_disk
		
		host.save() 