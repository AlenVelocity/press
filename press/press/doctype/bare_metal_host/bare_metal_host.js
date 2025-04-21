// Copyright (c) 2024, Frappe and contributors
// For license information, please see license.txt

frappe.ui.form.on('Bare Metal Host', {
	refresh: function(frm) {
		// Only allow provisioning if in Pending or Error state
		if (frm.doc.status === 'Pending' || frm.doc.status === 'Error') {
			frm.add_custom_button(__('Provision Host'), function() {
				frm.call('provision_host')
					.then(r => {
						if (r.message && r.message.status === 'Success') {
							frappe.show_alert({
								message: __('Host provisioning initiated successfully'),
								indicator: 'green'
							});
							frm.reload_doc();
						} else {
							frappe.msgprint({
								title: __('Provisioning Failed'),
								message: r.message.message || __('Failed to provision host'),
								indicator: 'red'
							});
						}
					});
			}, __('Actions'));
		}
		
		// Only allow setup as VM host if in Active state and not already a VM host
		if (frm.doc.status === 'Active' && !frm.doc.is_vm_host) {
			frm.add_custom_button(__('Setup as VM Host'), function() {
				frappe.confirm(
					__('This will install KVM/QEMU and other necessary packages. Continue?'),
					function() {
						frm.call('setup_vm_host')
							.then(r => {
								if (r.message && r.message.status === 'Success') {
									frappe.show_alert({
										message: __('VM host setup initiated successfully'),
										indicator: 'green'
									});
									frm.reload_doc();
								} else {
									frappe.msgprint({
										title: __('VM Host Setup Failed'),
										message: r.message.message || __('Failed to setup VM host'),
										indicator: 'red'
									});
								}
							});
					}
				);
			}, __('Actions'));
		}
		
		// Maintenance mode toggle
		if (frm.doc.status === 'Active') {
			frm.add_custom_button(__('Set to Maintenance'), function() {
				frm.call('set_maintenance_mode', { maintenance: true })
					.then(r => {
						if (r.message && r.message.status === 'Success') {
							frappe.show_alert({
								message: __('Host set to maintenance mode'),
								indicator: 'orange'
							});
							frm.reload_doc();
						}
					});
			}, __('Actions'));
		} else if (frm.doc.status === 'Maintenance') {
			frm.add_custom_button(__('Set to Active'), function() {
				frm.call('set_maintenance_mode', { maintenance: false })
					.then(r => {
						if (r.message && r.message.status === 'Success') {
							frappe.show_alert({
								message: __('Host set to active'),
								indicator: 'green'
							});
							frm.reload_doc();
						}
					});
			}, __('Actions'));
		}
		
		// Create VM button (only if this is a VM host)
		if (frm.doc.status === 'Active' && frm.doc.is_vm_host === 1) {
			frm.add_custom_button(__('Create Virtual Machine'), function() {
				const d = new frappe.ui.Dialog({
					title: __('Create Virtual Machine'),
					fields: [
						{
							label: __('VM Name'),
							fieldname: 'vm_name',
							fieldtype: 'Data',
							reqd: 1
						},
						{
							label: __('vCPUs'),
							fieldname: 'vcpus',
							fieldtype: 'Int',
							reqd: 1,
							default: 2
						},
						{
							label: __('Memory (MB)'),
							fieldname: 'memory_mb',
							fieldtype: 'Int',
							reqd: 1,
							default: 2048
						},
						{
							label: __('Disk Size (GB)'),
							fieldname: 'disk_gb',
							fieldtype: 'Int',
							reqd: 1,
							default: 20
						},
						{
							label: __('OS Variant'),
							fieldname: 'os_variant',
							fieldtype: 'Select',
							options: [
								'ubuntu22.04',
								'ubuntu20.04',
								'ubuntu18.04',
								'debian11',
								'debian10',
								'centos8',
								'centos7'
							],
							default: 'ubuntu22.04'
						}
					],
					primary_action_label: __('Create'),
					primary_action(values) {
						frm.call('create_virtual_machine', values)
							.then(r => {
								if (r.message && r.message.status === 'Success') {
									frappe.show_alert({
										message: __('VM creation initiated'),
										indicator: 'green'
									});
									d.hide();
									frm.reload_doc();
								} else {
									frappe.msgprint({
										title: __('VM Creation Failed'),
										message: r.message.message || __('Failed to create VM'),
										indicator: 'red'
									});
								}
							});
					}
				});
				d.show();
			}, __('Actions'));
		}
	}
}); 