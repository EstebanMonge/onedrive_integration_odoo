from odoo import models, fields

class SaleOrder(models.Model):
    _inherit = 'sale.order'
    onedrive_folder_url = fields.Char(string="OneDrive Folder URL")

    def action_open_onedrive_folder(self):

        self.ensure_one()

        # If already exists → just open
        if self.onedrive_folder_url:
            return {
                'type': 'ir.actions.act_url',
                'url': self.onedrive_folder_url,
                'target': 'new',
            }

        # Otherwise → create it once
        url = self.env['onedrive.dashboard']\
            .get_or_create_folder_for_record(self.name)

        # Save it
        self.onedrive_folder_url = url

        return {
            'type': 'ir.actions.act_url',
            'url': url,
            'target': 'new',
        }
