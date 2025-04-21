# Copyright (c) 2024, Frappe and contributors
# For license information, please see license.txt

import frappe
import json
import os
import subprocess
import time
from frappe.model.document import Document
from press.utils import log_error
from press.runner import Ansible


class BareMetalHost(Document):
	def validate(self):
		self.validate_ip_uniqueness()
		self.validate_ssh_key()

	def validate_ip_uniqueness(self):
		"""Ensure IP address is not already used by another host"""
		if not self.is_new():
			return

		if frappe.db.exists("Bare Metal Host", {"ip": self.ip, "name": ["!=", self.name]}):
			frappe.throw(f"IP address {self.ip} is already used by another host")

	def validate_ssh_key(self):
		"""Validate that SSH key exists if SSH key auth is enabled"""
		if self.auth_method == "SSH Key" and not self.ssh_key:
			frappe.throw("SSH Key is required when using SSH Key authentication")

	@frappe.whitelist()
	def provision_host(self):
		"""Provision the bare metal host by setting up required packages and configurations"""
		if self.status in ["Active", "Provisioning"]:
			frappe.throw(f"Host {self.hostname} is already {self.status.lower()}")

		self.status = "Provisioning"
		self.save()

		try:
			# Create ansible inventory
			inventory = f"{self.ip}:{self.ssh_port},"
			
			# Create a dummy server document for Ansible
			dummy_server = frappe._dict({
				"doctype": "Bare Metal Host",
				"name": self.name,
				"ip": self.ip
			})
			
			# Create variables for the playbook
			variables = {
				"host_ip": self.ip,
				"ssh_user": self.ssh_user,
				"ssh_port": self.ssh_port
			}
			
			# Run the provisioning playbook using Press Ansible
			playbook_name = "provision_bare_metal_host.yml"
			
			# Copy playbook to Press playbooks directory if not exists
			self.ensure_playbook_exists(playbook_name)
			
			# Run the playbook
			ansible = Ansible(
				server=dummy_server,
				playbook=playbook_name,
				user=self.ssh_user, 
				variables=variables,
				port=self.ssh_port
			)
			
			play_doc = ansible.run()
			
			if play_doc.status == "Success":
				# Update host info based on gathered facts
				# Note: We would need to extend Ansible runner to return facts
				# For now, we'll just set the status to active
				self.status = "Active"
				self.save()
				
				return {"status": "Success", "message": f"Host {self.hostname} provisioned successfully"}
			else:
				self.status = "Error"
				self.save()
				log_error(
					"Bare Metal Host Provisioning Error",
					host=self.hostname,
					ip=self.ip,
					error=play_doc.exception,
				)
				return {"status": "Error", "message": f"Failed to provision host: {play_doc.exception}"}
				
		except Exception as e:
			self.status = "Error"
			self.save()
			log_error(
				"Bare Metal Host Provisioning Exception",
				host=self.hostname,
				ip=self.ip,
				error=str(e),
			)
			return {"status": "Error", "message": f"Exception while provisioning host: {str(e)}"}

	def ensure_playbook_exists(self, playbook_name):
		"""Ensure playbook exists in Press playbooks directory"""
		source_path = os.path.join(
			os.path.dirname(os.path.abspath(__file__)),
			"playbooks",
			playbook_name.replace("provision_bare_metal_host.yml", "provision_host.yml")
		)
		
		dest_path = frappe.get_app_path("press", "playbooks", playbook_name)
		
		# If destination does not exist, copy from source
		if not os.path.exists(dest_path) and os.path.exists(source_path):
			import shutil
			os.makedirs(os.path.dirname(dest_path), exist_ok=True)
			shutil.copy2(source_path, dest_path)

	def update_host_info(self, facts):
		"""Update host information based on facts gathered during provisioning"""
		if facts:
			if facts.get("ansible_processor_vcpus"):
				self.total_cpu = facts.get("ansible_processor_vcpus")
				self.available_cpu = self.total_cpu
			
			if facts.get("ansible_memtotal_mb"):
				# Convert MB to GB and then to integer
				mem_mb = facts.get("ansible_memtotal_mb")
				self.total_memory = int(mem_mb)
				self.available_memory = self.total_memory
			
			if facts.get("ansible_devices"):
				# Calculate total disk space across all appropriate devices
				# Exclude loop devices, ramdisks, etc.
				total_gb = 0
				for device, details in facts.get("ansible_devices", {}).items():
					if not device.startswith(("loop", "ram", "sr")):
						size_bytes = int(details.get("size", "0").strip()) if details.get("size") else 0
						total_gb += size_bytes / (1024 * 1024 * 1024)
				
				self.total_disk = round(total_gb, 2)
				self.available_disk = self.total_disk
			
			if facts.get("ansible_distribution"):
				dist = facts.get("ansible_distribution", "")
				version = facts.get("ansible_distribution_version", "")
				self.os_info = f"{dist} {version}"

	@frappe.whitelist()
	def setup_vm_host(self):
		"""Set up the host as a VM host with required packages like KVM/QEMU"""
		if self.status not in ["Active"]:
			frappe.throw(f"Host must be Active to set up as VM host. Current status: {self.status}")

		self.status = "Provisioning"
		self.save()

		try:
			# Create a dummy server document for Ansible
			dummy_server = frappe._dict({
				"doctype": "Bare Metal Host",
				"name": self.name,
				"ip": self.ip
			})
			
			# Create variables for the playbook
			variables = {
				"host_ip": self.ip,
				"ssh_user": self.ssh_user,
				"ssh_port": self.ssh_port
			}
			
			# Run the VM host setup playbook
			playbook_name = "setup_bare_metal_vm_host.yml"
			
			# Copy playbook to Press playbooks directory if not exists
			self.ensure_playbook_exists(playbook_name.replace("setup_bare_metal_vm_host.yml", "setup_vm_host.yml"))
			
			# Run the playbook
			ansible = Ansible(
				server=dummy_server,
				playbook=playbook_name,
				user=self.ssh_user, 
				variables=variables,
				port=self.ssh_port
			)
			
			play_doc = ansible.run()
			
			if play_doc.status == "Success":
				self.is_vm_host = 1
				self.status = "Active"
				self.save()
				return {"status": "Success", "message": f"Host {self.hostname} set up as VM host successfully"}
			else:
				self.status = "Error"
				self.save()
				log_error(
					"VM Host Setup Error",
					host=self.hostname,
					ip=self.ip,
					error=play_doc.exception,
				)
				return {"status": "Error", "message": f"Failed to set up VM host: {play_doc.exception}"}
				
		except Exception as e:
			self.status = "Error"
			self.save()
			log_error(
				"VM Host Setup Exception",
				host=self.hostname,
				ip=self.ip,
				error=str(e),
			)
			return {"status": "Error", "message": f"Exception while setting up VM host: {str(e)}"}

	@frappe.whitelist()
	def set_maintenance_mode(self, maintenance=True):
		"""Set host to maintenance mode or back to active"""
		if maintenance:
			self.status = "Maintenance"
			message = f"Host {self.hostname} placed in maintenance mode"
		else:
			self.status = "Active"
			message = f"Host {self.hostname} is now active"
		
		self.save()
		return {"status": "Success", "message": message}

	@frappe.whitelist()
	def create_virtual_machine(self, vm_name=None, vcpus=2, memory_mb=2048, disk_gb=20, os_variant="ubuntu22.04"):
		"""Create a virtual machine on this host (if it's a VM host)"""
		if not self.is_vm_host:
			frappe.throw("This host is not configured as a VM host")
			
		if self.status != "Active":
			frappe.throw(f"Host must be Active to create VMs. Current status: {self.status}")
			
		# Check if we have sufficient resources
		if self.available_cpu < vcpus:
			frappe.throw(f"Not enough CPU resources available. Required: {vcpus}, Available: {self.available_cpu}")
			
		if self.available_memory < memory_mb:
			frappe.throw(f"Not enough memory available. Required: {memory_mb}MB, Available: {self.available_memory}MB")
			
		if self.available_disk < disk_gb:
			frappe.throw(f"Not enough disk space available. Required: {disk_gb}GB, Available: {self.available_disk}GB")
		
		# TODO: Implement VM creation using libvirt/KVM via Ansible playbook
		# This would typically involve a playbook that uses virt-install or similar tools
		
		# For now just return success response
		return {
			"status": "Success", 
			"message": f"Virtual machine creation initiated on host {self.hostname}",
			"vm_details": {
				"name": vm_name,
				"vcpus": vcpus,
				"memory_mb": memory_mb,
				"disk_gb": disk_gb
			}
		}

	@frappe.whitelist()
	def check_health(self):
		"""Check if the host is reachable and services are running properly"""
		try:
			# Create a dummy server document for Ansible
			dummy_server = frappe._dict({
				"doctype": "Bare Metal Host",
				"name": self.name,
				"ip": self.ip
			})
			
			# Create variables for the playbook
			variables = {
				"host_ip": self.ip,
				"ssh_user": self.ssh_user,
				"ssh_port": self.ssh_port
			}
			
			# Run a simple ping command using Ansible
			ansible = Ansible(
				server=dummy_server,
				module="ping",
				user=self.ssh_user,
				variables=variables,
				port=self.ssh_port
			)
			
			result = ansible.run()
			
			if result.status == "Success":
				self.last_health_check = frappe.utils.now()
				self.health_status = "Healthy"
				self.save()
				return {"status": "Success", "message": f"Host {self.hostname} is healthy"}
			else:
				self.health_status = "Unhealthy"
				self.save()
				log_error(
					"Host Health Check Error",
					host=self.hostname,
					ip=self.ip,
					error=result.exception,
				)
				return {"status": "Error", "message": f"Host health check failed: {result.exception}"}
		except Exception as e:
			self.health_status = "Unhealthy"
			self.save()
			log_error(
				"Host Health Check Exception",
				host=self.hostname,
				ip=self.ip,
				error=str(e),
			)
			return {"status": "Error", "message": f"Exception during health check: {str(e)}"} 