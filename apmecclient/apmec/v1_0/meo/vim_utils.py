# Copyright 2016 Brocade Communications Systems Inc
# All Rights Reserved.
#
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
import six.moves.urllib.parse as urlparse

from apmecclient.common import exceptions


def args2body_vim(config_param, vim):
    """Create additional args to vim body

    :param vim: vim request object
    :return: vim body with args populated
    """
    vim['vim_project'] = {'name': config_param.pop('project_name', ''),
                          'project_domain_name':
                              config_param.pop('project_domain_name', '')}
    if not vim['vim_project']['name']:
        raise exceptions.ApmecClientException(message='Project name '
                                              'must be specified',
                                              status_code=404)
    vim['auth_cred'] = {'username': config_param.pop('username', ''),
                        'password': config_param.pop('password', ''),
                        'user_domain_name':
                            config_param.pop('user_domain_name', '')}


def validate_auth_url(url):
    url_parts = urlparse.urlparse(url)
    if not url_parts.scheme or not url_parts.netloc:
        raise exceptions.ApmecClientException(message='Invalid auth URL')
    return url_parts
