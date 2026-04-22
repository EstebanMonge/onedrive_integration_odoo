# -*- coding: utf-8 -*-
###############################################################################
#
#   Cybrosys Technologies Pvt. Ltd.
#
#   Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#   Author: Jumana Haseen ( odoo@cybrosys.com )
#
#   You can modify it under the terms of the GNU AFFERO
#   GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#   You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#   (AGPL v3) along with this program.
#   If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
import json

import requests
from werkzeug import urls

from odoo import fields, models, _
from odoo.exceptions import UserError
from odoo.http import request


class ResConfigSettings(models.TransientModel):
    """
    This model represents the configuration settings for the OneDrive
    integration in Odoo.It allows users to configure various parameters for
    OneDrive integration, including client ID, client secret, access token,
    and folder ID.
    """
    _inherit = 'res.config.settings'

    onedrive_client = fields.Char(
        string='Onedrive Client ID', copy=False,
        config_parameter='onedrive_integration_odoo.client_id',
        help="Client ID for accessing OneDrive API")
    onedrive_client_secret = fields.Char(
        string='Onedrive Client Secret',
        config_parameter='onedrive_integration_odoo.client_secret',
        help="Client Secret for accessing OneDrive API")
    onedrive_tenant_id = fields.Char(
        string="Onedrive Tenant Id",
        config_parameter='onedrive_integration_odoo.tenant_id',
        help="Director (tenant) id for accessing OneDrive API")
    onedrive_access_token = fields.Char(
        string='Onedrive Access Token',
        help="Access Token for authenticating with OneDrive API")
    onedrive_refresh_token = fields.Char(
        string='Onedrive Refresh Token',
        help="Refresh Token for refreshing the access token")
    onedrive_folder = fields.Char(
        string='Folder ID', help="ID of the folder in OneDrive",
        config_parameter='onedrive_integration_odoo.folder_id')
    is_onedrive_enabled = fields.Boolean(
        string="Synchronize Onedrive with odoo",
        config_parameter='onedrive_integration_odoo.onedrive_button',
        help="Enable/Disable OneDrive integration")

    def action_get_onedrive_auth_code(self):

        client_id = self.env['ir.config_parameter'].get_param(
            'onedrive_integration_odoo.client_id')

        tenant_id = self.env['ir.config_parameter'].get_param(
            'onedrive_integration_odoo.tenant_id')

        base_url = self.env['ir.config_parameter'].get_param('web.base.url')

        redirect_uri = f"{base_url}/onedrive/authentication"

        state = json.dumps({
            'onedrive_config_id': self.id,
            'url_return': f"{base_url}/web"
        })

        params = {
            'client_id': client_id,
            'response_type': 'code',
            'redirect_uri': redirect_uri,
            'response_mode': 'query',
            'scope': 'offline_access openid Files.ReadWrite.All',  # 🔥 STRING, no lista
            'state': state,
            'prompt': 'consent'
        }

        authority = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/authorize"

        url = f"{authority}?{urls.url_encode(params)}"

        return {
            'type': 'ir.actions.act_url',
            'target': 'self',
            'url': url,
        }
