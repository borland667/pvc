"""
Virtual Machine Widgets

"""

import os
import time
import tarfile

import pyVmomi
import humanize
import requests

import pvc.widget.alarm
import pvc.widget.common
import pvc.widget.event
import pvc.widget.menu
import pvc.widget.form
import pvc.widget.gauge
import pvc.widget.vnc
import pvc.widget.network
import pvc.widget.performance
import pvc.widget.radiolist

from subprocess import Popen, PIPE

__all__ = [
    'VirtualMachineWidget',
    'VirtualMachineActionWidget',
    'VirtualMachineConsoleWidget',
    'VirtualMachinePowerWidget',
    'VirtualMachineExportWidget',
    'CreateVirtualMachineWidget',
]


class VirtualMachineWidget(object):
    def __init__(self, agent, dialog, obj):
        """
        Virtual Machine Widget

        Args:
            agent          (VConnector): A VConnector instance
            dialog      (dialog.Dialog): A Dialog instance
            obj    (vim.VirtualMachine): A VirtualMachine managed entity

        """
        self.agent = agent
        self.dialog = dialog
        self.obj = obj
        self.display()

    def display(self):
        items = [
            pvc.widget.menu.MenuItem(
                tag='General',
                description='General information',
                on_select=self.general_info
            ),
            pvc.widget.menu.MenuItem(
                tag='Resources',
                description='Resources usage information ',
                on_select=self.resources_info
            ),
            pvc.widget.menu.MenuItem(
                tag='Actions',
                description='Available Actions',
                on_select=VirtualMachineActionWidget,
                on_select_args=(self.agent, self.dialog, self.obj)
            ),
            pvc.widget.menu.MenuItem(
                tag='Power',
                description='Virtual Machine Power Options',
                on_select=VirtualMachinePowerWidget,
                on_select_args=(self.agent, self.dialog, self.obj)
            ),
            pvc.widget.menu.MenuItem(
                tag='Configuration',
                description='Virtual Machine settings'
            ),
            pvc.widget.menu.MenuItem(
                tag='Datastore',
                description='Datastores used by the VM',
                on_select=pvc.widget.common.datastore_menu,
                on_select_args=(self.agent, self.dialog, self.obj)
            ),
            pvc.widget.menu.MenuItem(
                tag='Network',
                description='Virtual Machine Networking',
                on_select=pvc.widget.common.network_menu,
                on_select_args=(self.agent, self.dialog, self.obj)
            ),
            pvc.widget.menu.MenuItem(
                tag='Performance',
                description='Performance Metrics',
                on_select=pvc.widget.performance.PerformanceProviderWidget,
                on_select_args=(self.agent, self.dialog, self.obj)
            ),
            pvc.widget.menu.MenuItem(
                tag='Template',
                description='Template Actions',
                on_select=VirtualMachineTemplateWidget,
                on_select_args=(self.agent, self.dialog, self.obj)
            ),
            pvc.widget.menu.MenuItem(
                tag='Events',
                description='View Events',
                on_select=pvc.widget.event.EventWidget,
                on_select_args=(self.agent, self.dialog, self.obj)
            ),
            pvc.widget.menu.MenuItem(
                tag='Alarms',
                description='View triggered alarms',
                on_select=pvc.widget.common.alarm_menu,
                on_select_args=(self.agent, self.dialog, self.obj)
            ),
            pvc.widget.menu.MenuItem(
                tag='Console',
                description='Launch Console',
                on_select=VirtualMachineConsoleWidget,
                on_select_args=(self.agent, self.dialog, self.obj)
            ),
        ]

        menu = pvc.widget.menu.Menu(
            items=items,
            dialog=self.dialog,
            title=self.obj.name,
            text='Select an item from menu'
        )

        menu.display()

    def general_info(self):
        """
        Virtual Machine general information

        """
        self.dialog.infobox(
            title=self.obj.name,
            text='Retrieving information ...'
        )

        elements = [
            pvc.widget.form.FormElement(
                label='Guest OS',
                item=self.obj.config.guestFullName if self.obj.config.guestFullName else 'Unknown'
            ),
            pvc.widget.form.FormElement(
                label='VM Version',
                item=self.obj.config.version
            ),
            pvc.widget.form.FormElement(
                label='CPU',
                item='{} vCPU(s)'.format(self.obj.config.hardware.numCPU)
            ),
            pvc.widget.form.FormElement(
                label='Memory',
                item='{} MB'.format(self.obj.config.hardware.memoryMB)
            ),
            pvc.widget.form.FormElement(
                label='Memory Overhead',
                item='{} MB'.format(self.obj.summary.quickStats.consumedOverheadMemory)
            ),
            pvc.widget.form.FormElement(
                label='VMware Tools Status',
                item=self.obj.guest.toolsRunningStatus
            ),
            pvc.widget.form.FormElement(
                label='VMware Tools Version',
                item=self.obj.guest.toolsVersionStatus
            ),
            pvc.widget.form.FormElement(
                label='IP Address',
                item=self.obj.guest.ipAddress if self.obj.guest.ipAddress else 'Unknown'
            ),
            pvc.widget.form.FormElement(
                label='DNS Name',
                item=self.obj.guest.hostName if self.obj.guest.hostName else 'Unknown'
            ),
            pvc.widget.form.FormElement(
                label='State',
                item=self.obj.runtime.powerState
            ),
            pvc.widget.form.FormElement(
                label='Host',
                item=self.obj.runtime.host.name
            ),
            pvc.widget.form.FormElement(
                label='Template',
                item=str(self.obj.config.template)
            ),
            pvc.widget.form.FormElement(
                label='Folder',
                item=self.obj.parent.name
            ),
            pvc.widget.form.FormElement(
                label='VMX Path',
                item=self.obj.config.files.vmPathName
            ),
        ]

        form = pvc.widget.form.Form(
            dialog=self.dialog,
            form_elements=elements,
            title=self.obj.name,
            text='Virtual Machine General Information'
        )

        form.display()

    def resources_info(self):
        """
        Resources usage information

        """
        self.dialog.infobox(
            title=self.obj.name,
            text='Retrieving information ...'
        )

        provisioned_storage = self.obj.summary.storage.committed + \
            self.obj.summary.storage.uncommitted

        elements = [
            pvc.widget.form.FormElement(
                label='Consumed Host CPU',
                item='{} MHz'.format(self.obj.summary.quickStats.overallCpuUsage)
            ),
            pvc.widget.form.FormElement(
                label='Consumed Host Memory',
                item='{} MB'.format(self.obj.summary.quickStats.hostMemoryUsage)
            ),
            pvc.widget.form.FormElement(
                label='Active Guest Memory',
                item='{} MB'.format(self.obj.summary.quickStats.guestMemoryUsage)
            ),
            pvc.widget.form.FormElement(
                label='Provisioned Storage',
                item=humanize.naturalsize(provisioned_storage, binary=True)
            ),
            pvc.widget.form.FormElement(
                label='Non-shared Storage',
                item=humanize.naturalsize(self.obj.summary.storage.unshared, binary=True)
            ),
            pvc.widget.form.FormElement(
                label='Used Storage',
                item=humanize.naturalsize(self.obj.summary.storage.committed, binary=True)
            ),
        ]

        form = pvc.widget.form.Form(
            dialog=self.dialog,
            form_elements=elements,
            title=self.obj.name,
            text='Virtual Machine Resources Usage Information'
        )

        return form.display()


class VirtualMachinePowerWidget(object):
    """
    Virtual Machine Power Menu Widget

    """
    def __init__(self, agent, dialog, obj):
        """
        Args:
            agent          (VConnector): A VConnector instance
            dialog      (dialog.Dialog): A Dialog instance
            obj    (vim.VirtualMachine): A VirtualMachine managed entity

        """
        self.agent = agent
        self.dialog = dialog
        self.obj = obj
        self.display()

    def display(self):
        items = [
            pvc.widget.menu.MenuItem(
                tag='Power On',
                description='Power On Virtual Machine',
                on_select=self.power_on
            ),
            pvc.widget.menu.MenuItem(
                tag='Power Off',
                description='Power Off Virtual Machine Off ',
                on_select=self.power_off
            ),
            pvc.widget.menu.MenuItem(
                tag='Suspend',
                description='Suspend Virtual Machine',
                on_select=self.suspend,
            ),
            pvc.widget.menu.MenuItem(
                tag='Reset',
                description='Reset Virtual Machine',
                on_select=self.reset
            ),
            pvc.widget.menu.MenuItem(
                tag='Shutdown',
                description='Shutdown Guest System',
                on_select=self.shutdown
            ),
            pvc.widget.menu.MenuItem(
                tag='Reboot',
                description='Reboot Guest System',
                on_select=self.reboot
            ),
        ]

        menu = pvc.widget.menu.Menu(
            items=items,
            dialog=self.dialog,
            title=self.obj.name,
            text='Select an action to be performed'
        )

        menu.display()

    def power_on(self):
        """
        Power on the virtual machine

        """
        if self.obj.runtime.powerState == pyVmomi.vim.VirtualMachinePowerState.poweredOn:
            self.dialog.msgbox(
                title=self.obj.name,
                text='Virtual Machine is already powered on.'
            )
            return

        task = self.obj.PowerOn()
        gauge = pvc.widget.gauge.TaskGauge(
            dialog=self.dialog,
            task=task,
            title=self.obj.name,
            text='Powering On Virtual Machine'
        )

        gauge.display()

    def power_off(self):
        """
        Power off the virtual machine

        """
        if self.obj.runtime.powerState == pyVmomi.vim.VirtualMachinePowerState.poweredOff:
            self.dialog.msgbox(
                title=self.obj.name,
                text='Virtual Machine is already powered off.'
            )
            return

        task = self.obj.PowerOff()
        gauge = pvc.widget.gauge.TaskGauge(
            dialog=self.dialog,
            task=task,
            title=self.obj.name,
            text='Powering Off Virtual Machine'
        )

        gauge.display()

    def suspend(self):
        """
        Suspend the virtual machine

        """
        if self.obj.runtime.powerState != pyVmomi.vim.VirtualMachinePowerState.poweredOn:
            self.dialog.msgbox(
                title=self.obj.name,
                text='Virtual Machine is not powered on, cannot suspend.'
            )
            return

        task = self.obj.Suspend()
        gauge = pvc.widget.gauge.TaskGauge(
            dialog=self.dialog,
            task=task,
            title=self.obj.name,
            text='Suspending Virtual Machine'
        )

        gauge.display()

    def reset(self):
        """
        Reset the virtual machine

        """
        if self.obj.runtime.powerState != pyVmomi.vim.VirtualMachinePowerState.poweredOn:
            self.dialog.msgbox(
                title=self.obj.name,
                text='Virtual Machine is not powered on, cannot reset.'
            )
            return

        task = self.obj.Reset()
        gauge = pvc.widget.gauge.TaskGauge(
            dialog=self.dialog,
            task=task,
            title=self.obj.name,
            text='Resetting Virtual Machine'
        )

        gauge.display()

    def shutdown(self):
        """
        Shutdown the virtual machine

        For a proper guest shutdown we need VMware Tools running

        """
        if self.obj.runtime.powerState != pyVmomi.vim.VirtualMachinePowerState.poweredOn:
            self.dialog.msgbox(
                title=self.obj.name,
                text='Virtual Machine is not powered on, cannot shutdown.'
            )
            return

        if self.obj.guest.toolsRunningStatus != pyVmomi.vim.VirtualMachineToolsRunningStatus.guestToolsRunning:
            self.dialog.msgbox(
                title=self.obj.name,
                text='VMware Tools is not running, cannot shutdown system'
            )
            return

        self.dialog.infobox(
            title=self.obj.name,
            text='Shutting down guest system ...'
        )
        self.obj.ShutdownGuest()

    def reboot(self):
        """
        Reboot the virtual machine

        For a proper guest reboot we need VMware Tools running

        """
        if self.obj.runtime.powerState != pyVmomi.vim.VirtualMachinePowerState.poweredOn:
            self.dialog.msgbox(
                title=self.obj.name,
                text='Virtual Machine is not powered on, cannot reboot.'
            )
            return

        if self.obj.guest.toolsRunningStatus != pyVmomi.vim.VirtualMachineToolsRunningStatus.guestToolsRunning:
            self.dialog.msgbox(
                title=self.obj.name,
                text='VMware Tools is not running, cannot reboot system'
            )
            return

        self.dialog.infobox(
            title=self.obj.name,
            text='Rebooting guest system ...'
        )
        self.obj.RebootGuest()


class VirtualMachineExportWidget(object):
    def __init__(self, agent, dialog, obj, create_ova):
        """
        Virtual Machine Export Widget

        Args:
            agent          (VConnector): A VConnector instance
            dialog      (dialog.Dialog): A Dialog instance
            obj    (vim.VirtualMachine): A VirtualMachine managed entity
            create_ova           (bool): If True then export VM into a single OVA file
                                         Otherwise create a folder of files (OVF)

        """
        self.agent = agent
        self.dialog = dialog
        self.obj = obj
        self.create_ova = create_ova
        self.display()

    def display(self):
        if self.obj.runtime.powerState != pyVmomi.vim.VirtualMachinePowerState.poweredOff:
            self.dialog.msgbox(
                title=self.obj.name,
                text='Virtual Machine must be powered off in order to be exported'
            )
            return

        code, path = self.dialog.dselect(
            title='Directory to save OVF template',
            filepath=''
        )

        path = os.path.join(path, self.obj.name)

        if code in (self.dialog.ESC, self.dialog.CANCEL):
            self.dialog.msgbox(
                title=self.obj.name,
                text='No destination directory specified'
            )
            return

        if not os.path.exists(path):
            os.makedirs(path)

        self.export_ovf_template(path=path)

    def export_ovf_template(self, path):
        """
        Exports a Virtual Machine into OVF/OVA template

        Args:
            path (str): Directory to save the OVF/OVA template

        """
        # TODO: Perform a dry-run and see if creating the
        #       OVF descriptor succeeds and then proceed with
        #       downloading the actual VMDK files

        self.dialog.infobox(
            title=self.obj.name,
            text='Initializing OVF export ...'
        )

        lease = self.obj.ExportVm()

        while True:
            if lease.state == pyVmomi.vim.HttpNfcLeaseState.initializing:
                lease.HttpNfcLeaseProgress(percent=0)
            elif lease.state == pyVmomi.vim.HttpNfcLeaseState.error:
                self.dialog.msgbox(
                    title=self.obj.name,
                    text=lease.error.msg
                )
                lease.HttpNfcLeaseAbort()
                return
            elif lease.state == pyVmomi.vim.HttpNfcLeaseState.ready:
                break
            time.sleep(0.5)

        percent = 0
        total_transfered_bytes = 0
        manifest = []
        ovf_files = []
        exported_disks = {}

        self.dialog.gauge_start(
            title='Exporting OVF template - {}'.format(self.obj.name)
        )

        for url in lease.info.deviceUrl:
            if not url.disk:  # skip non-vmdk disks
                continue

            self.dialog.gauge_update(
                percent=percent,
                text='Exporting {} ...\n'.format(url.targetId),
                update_text=True
            )

            if manifest:
                total_transfered_bytes = sum([m.capacity for m in manifest])

            disk_transfered_bytes = 0
            disk_file = os.path.join(path, '{}-{}'.format(self.obj.name, url.targetId))
            r = requests.get(url.url, verify=False, stream=True)

            with open(disk_file, 'wb') as f:
                for chunk in r.iter_content(chunk_size=512*1024):
                    if chunk:
                        disk_transfered_bytes += len(chunk)
                        percent = round(
                            (total_transfered_bytes + disk_transfered_bytes) / 1024 /
                            lease.info.totalDiskCapacityInKB * 100
                        )
                        self.dialog.gauge_update(percent=percent)
                        lease.HttpNfcLeaseProgress(percent=percent)
                        f.write(chunk)

            m = [me for me in lease.HttpNfcLeaseGetManifest() if me.key == url.key].pop()
            manifest.append(m)

            of = pyVmomi.vim.OvfManager.OvfFile(
                capacity=m.capacity,
                deviceId=m.key,
                path=os.path.basename(disk_file),
                populatedSize=m.populatedSize,
                size=disk_transfered_bytes,
            )
            ovf_files.append(of)

            exported_disks[url.key] = url.targetId
            total_transfered_bytes = sum([me.capacity for me in manifest])
            percent = round(
                total_transfered_bytes / 1024 / lease.info.totalDiskCapacityInKB * 100
            )
            self.dialog.gauge_update(percent)
            lease.HttpNfcLeaseProgress(percent=percent)

        # Create OVF manifest and descriptor files
        self.dialog.gauge_stop()
        self.create_manifest_file(
            path=path,
            manifest=manifest,
            disks=exported_disks
        )

        self.create_ovf_descriptor(
            path=path,
            ovf_files=ovf_files
        )

        lease.HttpNfcLeaseComplete()

        if self.create_ova:
            self.create_ova_file(
                path=path,
                disks=exported_disks.values()
            )

        self.dialog.msgbox(
            title=self.obj.name,
            text='Export successful. Files saved in:\n\n{}\n'.format(path)
        )

    def create_manifest_file(self, path, manifest, disks):
        """
        Creates the OVF manifest file

        Args:
            path      (str): Path to the exported disks
            manifest (list): A list of vim.HttpNfcLease.ManifestEntry instances
            disks    (dict): A mapping of the disk keys and target ids

        """
        self.dialog.infobox(
            title=self.obj.name,
            text='Creating OVF manifest ...'
        )

        with open(os.path.join(path, '{}.mf'.format(self.obj.name)), 'w') as f:
            for entry in manifest:
                f.write('SHA1({}-{})= {}\n'.format(
                    self.obj.name,
                    disks[entry.key],
                    entry.sha1)
                )

    def create_ovf_descriptor(self, path, ovf_files):
        """
        Creates the OVF descriptor file

        Args:
            path       (str): Path to the exported disks
            ovf_files (list): A list of vim.OvfManager.OvfFile instances

        """
        self.dialog.infobox(
            title=self.obj.name,
            text='Creating OVF descriptor ...'
        )

        cdp = pyVmomi.vim.OvfManager.CreateDescriptorParams(
            ovfFiles=ovf_files
        )

        dr = self.agent.si.content.ovfManager.CreateDescriptor(
            obj=self.obj,
            cdp=cdp
        )

        if dr.warning:
            self.dialog.msgbox(
                title='Warning - {}'.format(self.obj.name),
                text=str(dr.warning)
            )

        if dr.error:
            self.dialog.msgbox(
                title='Error - {}'.format(self.obj.name),
                text=str(dr.error)
            )

        with open(os.path.join(path, '{}.ovf'.format(self.obj.name)), 'w') as f:
            f.write(dr.ovfDescriptor)

    def create_ova_file(self, path, disks):
        """
        Creates a single OVA file of the exported VM

        Args:
            path   (str): Path to the exported disks
            disks (list): A list of the downloaded disks

        """
        self.dialog.infobox(
            title=self.obj.name,
            text='Creating OVA file ...'
        )

        old_cwd = os.getcwd()
        os.chdir(path)

        ova = tarfile.open('{}.ova'.format(self.obj.name), 'w')

        # Add descriptor and manifest files first
        descriptor = '{}.ovf'.format(self.obj.name)
        manifest = '{}.mf'.format(self.obj.name)
        ova.add(descriptor)
        ova.add(manifest)

        # Now add the VMDK disks
        for disk in disks:
            ova.add('{}-{}'.format(self.obj.name, disk))

        ova.close()

        # Cleanup disks, manifest and descriptor files
        os.unlink(manifest)
        os.unlink(descriptor)
        for disk in disks:
            os.unlink('{}-{}'.format(self.obj.name, disk))

        os.chdir(old_cwd)


class VirtualMachineConsoleWidget(object):
    def __init__(self, agent, dialog, obj):
        """
        Virtual Machine Console Widget

        Args:
            agent          (VConnector): A VConnector instance
            dialog      (dialog.Dialog): A Dialog instance
            obj    (vim.VirtualMachine): A VirtualMachine managed entity

        """
        self.agent = agent
        self.dialog = dialog
        self.obj = obj
        self.display()

    def display(self):
        items = [
            pvc.widget.menu.MenuItem(
                tag='VNC',
                description='Launch VNC Console',
                on_select=pvc.widget.vnc.VncWidget,
                on_select_args=(self.dialog, self.obj)
            ),
            pvc.widget.menu.MenuItem(
                tag='VMware Player',
                description='Launch VMware Player Console',
                on_select=self.vmplayer_console,
            ),
        ]

        menu = pvc.widget.menu.Menu(
            items=items,
            dialog=self.dialog,
            title=self.obj.name,
            text='Select console to be launched'
        )

        menu.display()

    def vmplayer_console(self):
        """
        Launch a VMware Player console to the Virtual Machine

        In order to establish a remote console session to the
        Virtual Machine we run VMware Player this way:

            $ vmplayer -h <hostname> -p <ticket> -M <managed-object-id>

        Where <ticket> is an acquired ticket as returned by a
        previous call to AcquireCloneTicket().

        """
        self.dialog.infobox(
            title=self.obj.name,
            text='Launching console ...'
        )

        ticket = self.agent.si.content.sessionManager.AcquireCloneTicket()

        try:
            Popen(
                args=['vmplayer', '-h', self.agent.host, '-p', ticket, '-M', self.obj._moId],
                stdout=PIPE,
                stderr=PIPE
            )
        except OSError as e:
            self.dialog.msgbox(
                title=self.obj.name,
                text='Cannot launch console: \n{}\n'.format(e)
            )
            return

        # Give it some time to start up the console
        time.sleep(3)


class VirtualMachineTemplateWidget(object):
    def __init__(self, agent, dialog, obj):
        """
        Virtual Machine Template Widget

        Args:
            agent          (VConnector): A VConnector instance
            dialog      (dialog.Dialog): A Dialog instance
            obj    (vim.VirtualMachine): A VirtualMachine managed entity

        """
        self.agent = agent
        self.dialog = dialog
        self.obj = obj
        self.display()

    def display(self):
        items = [
            pvc.widget.menu.MenuItem(
                tag='Mark Template',
                description='Mark Virtual Machine as template',
                on_select=self.mark_as_template
            ),
            pvc.widget.menu.MenuItem(
                tag='Mark VM',
                description='Mark template as Virtual Machine',
                on_select=self.mark_as_virtual_machine
            ),
            pvc.widget.menu.MenuItem(
                tag='Export OVA',
                description='Export as single file (OVA)',
                on_select=VirtualMachineExportWidget,
                on_select_args=(self.agent, self.dialog, self.obj, True)
            ),
            pvc.widget.menu.MenuItem(
                tag='Export OVF',
                description='Export as directory of files (OVF)',
                on_select=VirtualMachineExportWidget,
                on_select_args=(self.agent, self.dialog, self.obj, False)
            ),
        ]

        menu = pvc.widget.menu.Menu(
            dialog=self.dialog,
            items=items,
            title=self.obj.name,
            text='Select an action to be performed'
        )

        menu.display()

    def mark_as_template(self):
        """
        Mark Virtual Machine as a template

        """
        if self.obj.runtime.powerState != pyVmomi.vim.VirtualMachinePowerState.poweredOff:
            self.dialog.msgbox(
                title=self.obj.name,
                text='Virtual Machine must be powered off first'
            )
            return

        self.dialog.infobox(
            title=self.obj.name,
            text='Marking {} as template ...'.format(self.obj.name)
        )

        try:
            self.obj.MarkAsTemplate()
        except Exception as e:
            self.dialog.msgbox(
                title=self.obj.name,
                text=e.msg
            )

    def mark_as_virtual_machine(self):
        """
        Marks a template as a Virtual Machine

        """
        self.dialog.infobox(
            title=self.obj.name,
            text='Marking {} as virtual machine ...'.format(self.obj.name)
        )

        try:
            self.obj.MarkAsVirtualMachine()
        except Exception as e:
            self.dialog.msgbox(
                title=self.obj.name,
                text=e.msg
            )


class VirtualMachineActionWidget(object):
    def __init__(self, agent, dialog, obj):
        """
        Virtual Machine Action Widget

        Args:
            agent          (VConnector): A VConnector instance
            dialog      (dialog.Dialog): A Dialog instance
            obj    (vim.VirtualMachine): A VirtualMachine managed entity

        """
        self.agent = agent
        self.dialog = dialog
        self.obj = obj
        self.display()

    def display(self):
        items = [
            pvc.widget.menu.MenuItem(
                tag='Rename',
                description='Rename Virtual Machine',
                on_select=pvc.widget.common.rename,
                on_select_args=(self.obj, self.dialog)
            ),
            pvc.widget.menu.MenuItem(
                tag='Unregister',
                description='Remove from inventory',
                on_select=self.unregister
            ),
            pvc.widget.menu.MenuItem(
                tag='Delete',
                description='Delete from disk',
                on_select=pvc.widget.common.remove,
                on_select_args=(self.obj, self.dialog)
            ),
        ]

        menu = pvc.widget.menu.Menu(
            dialog=self.dialog,
            items=items,
            title=self.obj.name,
            text='Select an action to be performed'
        )

        menu.display()

    def unregister(self):
        """
        Unregister the VM from inventory

        """
        code = self.dialog.yesno(
            title='Confirm remove',
            text='Remove {} from inventory?'.format(self.obj.name)
        )

        if code in (self.dialog.ESC, self.dialog.CANCEL):
            return

        self.dialog.infobox(
            title=self.obj.name,
            text='Removing {} from inventory ...'.format(self.obj.name)
        )

        self.obj.UnregisterVM()


class CreateVirtualMachineWidget(object):
    def __init__(self, agent, dialog, datacenter=None, cluster=None, host=None):
        """
        Widget for creating a new Virtual Machine

        Args:
            agent                      (VConnector): A VConnector instance
            dialog                  (dialog.Dialog): A Dialog instance
            datacenter             (vim.Datacenter): A vim.Datacenter instance
            cluster    (vim.ClusterComputeResource): A vim.CluterComputeResource instance
            host                   (vim.HostSystem): A vim.HostSystem instance

        """
        self.agent = agent
        self.dialog = dialog
        self.datacenter = datacenter
        self.cluster = cluster
        self.host = host
        self.display()

    def display(self):
        if not self.datacenter:
            self.datacenter = self.select_datacenter()
            if not self.datacenter:
                return

        if not self.cluster:
            self.cluster = self.select_cluster(folder=self.datacenter)
            if not self.cluster:
                return

        if not self.select_host(cluster=self.cluster):
            return

        if self.host:
            datastore = self.select_datastore(obj=self.host)
        else:
            datastore = self.select_datastore(obj=self.cluster)

        if not datastore:
            return

        folder = self.datacenter.vmFolder
        pool = self.cluster.resourcePool
        vmx_version = self.select_vmx_version(obj=self.cluster)

    def select_datacenter(self):
        """
        Select datacenter for Virtual Machine placement

        Returns:
            A vim.Datacenter managed entity upon successfuly selecting
            an existing vim.Datacenter instance, None otherwise

        """
        datacenter = pvc.widget.common.choose_datacenter(
            agent=self.agent,
            dialog=self.dialog
        )

        if not datacenter:
            return

        if not datacenter.hostFolder.childEntity:
            self.dialog.msgbox(
                title='Create New Virtual Machine',
                text='No compute resources found in datacenter {}'.format(datacenter.name)
            )
            return

        return datacenter

    def select_cluster(self, folder):
        """
        Select a cluster for Virtual Machine placement

        Args:
            folder (vim.Folder): A vim.Folder instance

        Returns:
            A vim.ClusterComputeResource managed entity upon successufuly
            selecting an existing cluster, None otherwise

        """
        cluster = pvc.widget.common.choose_cluster(
            agent=self.agent,
            dialog=self.dialog,
            folder=folder
        )

        if not cluster:
            return

        if not cluster.host:
            self.dialog.msgbox(
                title='Create New Virtual Machine',
                text='No valid hosts found in cluster {}'.format(cluster.name)
            )
            return

        return cluster

    def select_host(self, cluster):
        """
        Select host for Virtual Machine placement

        If a target host has been provided use that host for the
        Virtual Machine placement.

        If the cluster has DRS enabled in Fully Automated mode then
        let vSphere decide where to place the Virtual Machine instead.

        Args:
            cluster (vim.ClusterComputeResource): A cluster managed entity

        Returns:
            True on successfully selecting a host or if the cluster is
            configured with DRS in fully automated mode allowing for
            dynamic Virtual Machine placement, otherwise returns False.

        """
        drs_config = cluster.configuration.drsConfig
        drs_enabled = drs_config.enabled
        drs_fully_automated = drs_config.defaultVmBehavior == pyVmomi.vim.cluster.DrsConfigInfo.DrsBehavior.fullyAutomated
        dynamic_placement = drs_enabled and drs_fully_automated

        if not self.host and not dynamic_placement:
            self.host = pvc.widget.common.choose_host(
                agent=self.agent,
                dialog=self.dialog,
                folder=cluster
            )

            if not self.host:
                self.dialog.msgbox(
                    title='Create New Virtual Machine',
                    text='No valid host selected'
                )
                return False

        return True

    def select_datastore(self, obj):
        """
        Select datastore for Virtual Machine placement

        Args:
            obj (vim.ManagedEntity): A Managed Entity containing datastores

        Returns:
            A vim.Datastore managed entity upon successfully
            selecting a datastore, None otherwise

        """
        if not obj.datastore:
            self.dialog.msgbox(
                title='Create New Virtual Machine',
                text='No datastores found on {}'.format(obj.name)
            )
            return

        datastore = pvc.widget.common.choose_datastore(
            agent=self.agent,
            dialog=self.dialog,
            obj=obj
        )

        return datastore

    def select_vmx_version(self, obj):
        """
        Select a VMX version for the Virtual Machine

        Args:
            obj (vim.ComputeResource): Entity to query for supported versions

        """
        self.dialog.infobox(
            text='Retrieving information ...'
        )

        versions = obj.environmentBrowser.QueryConfigOptionDescriptor()
        items = [
            pvc.widget.radiolist.RadioListItem(
                tag=v.key,
                description=v.description
            ) for v in versions if v.createSupported
        ]

        radiolist = pvc.widget.radiolist.RadioList(
            items=items,
            dialog=self.dialog,
            title='Create New Virtual Machine',
            text='Select Virtual Machine hardware version'
        )

        code, tag = radiolist.display()

        if code in (self.dialog.CANCEL, self.dialog.ESC) or not tag:
            return

        return tag
