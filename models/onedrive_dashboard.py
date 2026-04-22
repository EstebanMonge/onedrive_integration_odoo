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
import logging
import requests
from datetime import timedelta
from odoo import fields, models
from odoo.http import request
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class OneDriveDashboard(models.Model):
    """
    Generate refresh and  access token
    """
    _name = 'onedrive.dashboard'
    _description = "Generate access and refresh tokens "

    onedrive_access_token = fields.Char(
        string="OneDrive Access Token",
        store=True,
        help="Access token for authenticating and accessing OneDrive APIs.")
    onedrive_refresh_token = fields.Char(
        string="OneDrive Refresh Token",
        help="Refresh token for obtaining a new access token when the current "
             "one expires.")
    token_expiry_date = fields.Char(
        string="OneDrive Token Validity",
        help="Validity period of the access token, indicating until when it is"
             " valid.")
    upload_file = fields.Binary(
        string="Upload File",
        help="Binary field to store the uploaded file.")

    def get_tokens(self, authorize_code):
        """
        Generate onedrive tokens from authorization code
        """
        data = {
            'code': authorize_code,
            'client_id': self.env['ir.config_parameter'].get_param(
                'onedrive_integration_odoo.client_id', ''),
            'client_secret': self.env['ir.config_parameter'].get_param(
                'onedrive_integration_odoo.client_secret', ''),
            'grant_type': 'authorization_code',
            'scope': ['offline_access openid Files.ReadWrite.All'],
            'redirect_uri': request.env['ir.config_parameter'].get_param(
                'web.base.url') + '/onedrive/authentication'
        }
        try:
            res = requests.post(
                "https://login.microsoftonline.com/common/oauth2/v2.0/token",
                data=data,
                headers={"content-type": "application/x-www-form-urlencoded"})
            res.raise_for_status()
            response = res.content and res.json() or {}
            if response:
                expires_in = response.get('expires_in')
                self.env['onedrive.dashboard'].create({
                    'onedrive_access_token': response.get('access_token'),
                    'onedrive_refresh_token': response.get('refresh_token'),
                    'token_expiry_date': fields.Datetime.now() + timedelta(
                        seconds=expires_in) if expires_in else False,
                })
        except requests.HTTPError as error:
            _logger.exception("Bad microsoft onedrive request : %s !",
                              error.response.content)
            raise error

    def action_synchronize_onedrive(self):
        """
        Pass the files to javascript
        """
        record = self.search([], order='id desc', limit=1)
        if not record:
            return False
        if record.token_expiry_date <= str(fields.Datetime.now()):
            record.generate_onedrive_refresh_token()
        folder = self.env['ir.config_parameter'].get_param(
            'onedrive_integration_odoo.folder_id', '')
        if not folder:return False
        url = "https://graph.microsoft.com/v1.0/me/drive/root:%s:/children" % folder
        response = requests.request("GET", url, headers={
            'Authorization': 'Bearer ' + record.onedrive_access_token },
                                    data={})
        message = json.loads(response.content)
        if 'error' in message:
            return ['error', message['error']['code'],
                    message['error']['message']]
        files = {}
        for item in response.json().get('value', []):
            files[item['name']] = {
                'type': 'folder' if 'folder' in item else 'file',
                'downloadUrl': item.get('@microsoft.graph.downloadUrl'),
                'webUrl': item.get('webUrl'),
            }

#            if 'folder' in file:
#                files[file['name']] = {
#                    'type': 'folder',
#                    'id': file.get('id')
#                }

#            elif '@microsoft.graph.downloadUrl' in file:
#                files[file['name']] = {
#                    'type': 'file',
#                    'url': file['@microsoft.graph.downloadUrl']
#                }
        return files

    def generate_onedrive_refresh_token(self):
        """
        Generate onedrive access token from refresh token if expired
        """
        data = {
            'client_id': self.env['ir.config_parameter'].get_param(
                'onedrive_integration_odoo.client_id', ''),
            'client_secret': self.env['ir.config_parameter'].get_param(
                'onedrive_integration_odoo.client_secret', ''),
            'scope': ['offline_access openid Files.ReadWrite.All'],
            'grant_type': "refresh_token",
            'redirect_uri': request.env['ir.config_parameter'].get_param(
                'web.base.url') + '/onedrive/authentication',
            'refresh_token': self.onedrive_refresh_token
        }
        try:
            res = requests.post(
                "https://login.microsoftonline.com/common/oauth2/v2.0/token",
                data=data,
                headers={"Content-type": "application/x-www-form-urlencoded"})
            res.raise_for_status()
            response = res.content and res.json() or {}
            if response:
                expires_in = response.get('expires_in')
                self.write({
                    'onedrive_access_token': response.get('access_token'),
                    'onedrive_refresh_token': response.get('refresh_token'),
                    'token_expiry_date': fields.Datetime.now() + timedelta(
                        seconds=expires_in) if expires_in else False,
                })
        except requests.HTTPError as error:
            _logger.exception("Bad microsoft onedrive request : %s !",
                              error.response.content)
            raise error

    def upload_file_to_onedrive(self, file_content, file_name, folder=None):

        token = self.search([], order='id desc', limit=1)

        if not token:
            raise UserError("No token found")

        if not folder:
            folder = self.env['ir.config_parameter'].get_param(
                'onedrive_integration_odoo.folder_id', ''
            )

        if not folder:
            raise UserError("Folder not configured")

        if token.token_expiry_date:
            expiry = fields.Datetime.from_string(token.token_expiry_date)
            if expiry <= fields.Datetime.now():
                token.generate_onedrive_refresh_token()

        url = f"https://graph.microsoft.com/v1.0/me/drive/root:{folder}/{file_name}:/content"

        headers = {
            'Authorization': 'Bearer ' + token.onedrive_access_token,
            'Content-Type': 'application/octet-stream'
        }

        response = requests.put(url, headers=headers, data=file_content)
        result = response.json()

        if 'error' in result:
            raise UserError(str(result))

        return result

    def create_folder_onedrive(self, folder_name):

        token = self.search([], order='id desc', limit=1)

        if not token:
            return {'error': 'No token found'}

        folder = self.env['ir.config_parameter'].get_param(
            'onedrive_integration_odoo.folder_id', ''
        )

        if not folder:
            return {'error': 'Folder not configured'}

        if token.token_expiry_date:
            expiry = fields.Datetime.from_string(token.token_expiry_date)
            if expiry <= fields.Datetime.now():
                token.generate_onedrive_refresh_token()

        headers = {
            'Authorization': 'Bearer ' + token.onedrive_access_token,
            'Content-Type': 'application/json'
        }

        search_url = f"https://graph.microsoft.com/v1.0/me/drive/root:{folder}:/children"

        response = requests.get(search_url, headers=headers)
        result = response.json()

        if 'error' in result:
            return {'error': result['error']['message']}

        for item in result.get('value', []):
            if item.get('name') == folder_name and 'folder' in item:
                return {'error': f'Folder "{folder_name}" already exists'}

        create_url = f"https://graph.microsoft.com/v1.0/me/drive/root:{folder}:/children"

        data = {
            "name": folder_name,
            "folder": {},
            "@microsoft.graph.conflictBehavior": "fail"  # 👈 extra seguridad
        }

        try:
            response = requests.post(create_url, headers=headers, json=data)
            result = response.json()

            if 'error' in result:
                return {'error': result['error']['message']}

            return {
                'success': True,
                'name': result.get('name'),
                'id': result.get('id')
            }

        except Exception as e:
            _logger.exception("Error creating folder in OneDrive")
            return {'error': str(e)}

    def get_or_create_folder_for_record(self, folder_name):

        token = self.search([], order='id desc', limit=1)

        if not token:
            raise UserError("No token found")

        base_folder = self.env['ir.config_parameter'].get_param(
            'onedrive_integration_odoo.folder_id', ''
        )

        headers = {
            'Authorization': 'Bearer ' + token.onedrive_access_token,
            'Content-Type': 'application/json'
        }

        # Step 1: check if exists
        list_url = f"https://graph.microsoft.com/v1.0/me/drive/root:{base_folder}:/children"
        response = requests.get(list_url, headers=headers).json()

        for item in response.get('value', []):
            if item.get('name') == folder_name:
                return item.get('webUrl')

        # Step 2: create folder
        create_url = f"https://graph.microsoft.com/v1.0/me/drive/root:{base_folder}:/children"

        payload = {
            "name": folder_name,
            "folder": {},
            "@microsoft.graph.conflictBehavior": "fail"
        }

        result = requests.post(create_url, headers=headers, json=payload).json()

        if 'error' in result:
            raise UserError(str(result))

        return result.get('webUrl')
