/** @odoo-modules */
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component } from "@odoo/owl";
import { jsonrpc } from "@web/core/network/rpc_service";
const actionRegistry = registry.category("actions");
import { useRef } from "@odoo/owl";
class OnedriveDashboard extends Component{
setup() {
        super.setup();
        this.orm = useService("orm");
        this.action = useService("action");
        this.inputRef = useRef("all_files");
        this.synchronize();
    }
//         * Opens a file upload dialog on click of the "Upload" button.
//         *
//         * @param {Object} ev - The click event object.
//         */
        async upload(){
            this.action.doAction({
                name: "Upload File",
                type: 'ir.actions.act_window',
                res_model: 'upload.file',
                view_mode: 'form',
                view_type: 'form',
                views: [[false, 'form']],
                target: 'new',
            });
        }
        /**
         * Retrieves and displays files from OneDrive on click of the "Import" button.
         *
         * @param {Object} ev - The click event object.
         */
        async synchronize(){
            var self = this;
            var result = await this.orm.call('onedrive.dashboard',
            "action_synchronize_onedrive",[' '])
            if (!result) {
                this.action.doAction({
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'message': 'Please setup credentials',
                        'type': 'warning',
                        'sticky': false,
                    }
                    });
            }
            else if (result[0] === 'error') {
                if (result[1] === 'itemNotFound') {
                    // Display a notification if the folder is not found
                    this.action.doAction({
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'message': 'Error: Folder not found.',
                            'type': 'warning',
                            'sticky': false,
                        }
                    });
                }
                else {
                    // Display a notification for other errors
                    this.action.doAction({
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'message': 'Error:' + result[2],
                            'type': 'warning',
                            'sticky': false,
                        }
                    });
                }
            } else {
                // Empty the onedrive_files div and append the files retrieved
                this.inputRef.el.innerHTML = '';
                $.each(Object.keys(result), function (index, name) {
                    let item = result[name];
                    if (item.type === 'folder') {
                        $('#onedrive_files').append(
                            '<div class="col-sm-6 card" align="center">' +
                            '<a href="' + item.webUrl + '" target="_blank">' +
                            '<img class="card-img top" src="/onedrive_integration_odoo/static/src/img/file_icon.png"/>' +
                            name +
                            '</a>' +
                            '</div>'
                        );
                    } else {
                        $('#onedrive_files').append(
                            '<div class="col-sm-6 card" align="center">' +
                            '<a href="' + item.downloadUrl + '">' +
                            '<img class="card-img top" src="/onedrive_integration_odoo/static/src/img/file_icon.png"/>' +
                            name +
                            '</a>' +
                            '</div>'
                        );
                    }
                });
            }
        }
        /**
         * Filters files displayed based on file type (e.g., image, all files).
         *
         * @param {Object} ev - The click event object.
         */
        async createFolder() {
            const folderName = prompt("Enter folder name");

            if (!folderName) {
                return;
            }

            try {
                const result = await this.orm.call(
                    'onedrive.dashboard',
                    'create_folder_onedrive',
                    [[], folderName]
                );
                if (result && result.error) {
                    this.action.doAction({
                        type: 'ir.actions.client',
                        tag: 'display_notification',
                        params: {
                            message: 'Error: ' + result.error,
                             type: 'warning',
                        }
                    });
                } else {
                    this.action.doAction({
                        type: 'ir.actions.client',
                        tag: 'display_notification',
                        params: {
                            message: 'Folder created successfully',
                            type: 'success',
                        }
                    });

                    this.synchronize();
                }

            } catch (error) {
                this.action.doAction({
                    type: 'ir.actions.client',
                    tag: 'display_notification',
                    params: {
                        message: 'Failed: ' + error.message,
                        type: 'danger',
                    }
                });
            }
        }
        async filter_file_type(ev) {
            var value = ev.currentTarget.getAttribute('value');
            $.each($('.card'), function (index, name) {
                $(this).hide();
                var file_type = (name.textContent).slice(((name.textContent).lastIndexOf(".") - 1 >>> 0) + 2);
                if (file_type == value) {
                    $(this).show();
                }
                if (value == 'allfiles') {
                    $(this).show();
                }
                if (value == 'image') {
                    if (file_type == 'jpeg' || file_type == 'jpg' || file_type == 'png') {
                        $(this).show();
                    }
                }
            });
        }
    }
OnedriveDashboard.template = "OnedriveDashboard";
registry.category("actions").add("onedrive_dashboard", OnedriveDashboard)
