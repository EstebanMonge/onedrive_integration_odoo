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
from odoo import http
from odoo.http import request

class OnedriveAuth(http.Controller):

    @http.route('/onedrive/authentication', type='http', auth="user")
    def oauth2callback(self, **kw):

        # 🔴 Manejo de errores de Microsoft
        if kw.get('error'):
            return f"Microsoft error: {kw.get('error_description', kw.get('error'))}"

        code = kw.get('code')
        if not code:
            return "No authorization code received"

        # 🔴 Manejo seguro de state
        state_raw = kw.get('state')
        if not state_raw:
            return "Missing state parameter"

        try:
            state = json.loads(state_raw)
        except Exception:
            return "Invalid state format"

        onedrive_config_id = request.env['onedrive.dashboard'].sudo().browse(
            state.get('onedrive_config_id')
        )

        # 🔥 Aquí ocurre el intercambio de tokens
        onedrive_config_id.get_tokens(code)

        return request.redirect(state.get('url_return', '/web'))
