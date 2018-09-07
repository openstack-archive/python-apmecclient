# Copyright 2012 OpenStack Foundation.
# Copyright 2015 Hewlett-Packard Development Company, L.P.
# All Rights Reserved
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
#

import logging
import time

import requests
import six.moves.urllib.parse as urlparse

from apmecclient import client
from apmecclient.common import constants
from apmecclient.common import exceptions
from apmecclient.common import serializer
from apmecclient.common import utils
from apmecclient.i18n import _

_logger = logging.getLogger(__name__)
DEFAULT_DESC_LENGTH = 25
DEFAULT_ERROR_REASON_LENGTH = 100


def exception_handler_v10(status_code, error_content):
    """Exception handler for API v1.0 client.

    This routine generates the appropriate Apmec exception according to
    the contents of the response body.

    :param status_code: HTTP error status code
    :param error_content: deserialized body of error response
    """
    error_dict = None
    if isinstance(error_content, dict):
        error_dict = error_content.get('ApmecError')
    # Find real error type
    bad_apmec_error_flag = False
    if error_dict:
        # If Apmec key is found, it will definitely contain
        # a 'message' and 'type' keys?
        try:
            error_type = error_dict['type']
            error_message = error_dict['message']
            if error_dict['detail']:
                error_message += "\n" + error_dict['detail']
        except Exception:
            bad_apmec_error_flag = True
        if not bad_apmec_error_flag:
            # If corresponding exception is defined, use it.
            client_exc = getattr(exceptions, '%sClient' % error_type, None)
            # Otherwise look up per status-code client exception
            if not client_exc:
                client_exc = exceptions.HTTP_EXCEPTION_MAP.get(status_code)
            if client_exc:
                raise client_exc(message=error_message,
                                 status_code=status_code)
            else:
                raise exceptions.ApmecClientException(
                    status_code=status_code, message=error_message)
        else:
            raise exceptions.ApmecClientException(status_code=status_code,
                                                   message=error_dict)
    else:
        message = None
        if isinstance(error_content, dict):
            message = error_content.get('message')
        if message:
            raise exceptions.ApmecClientException(status_code=status_code,
                                                   message=message)

    # If we end up here the exception was not a apmec error
    msg = "%s-%s" % (status_code, error_content)
    raise exceptions.ApmecClientException(status_code=status_code,
                                           message=msg)


class APIParamsCall(object):
    """A Decorator to support formating and tenant overriding and filters."""

    def __init__(self, function):
        self.function = function

    def __get__(self, instance, owner):
        def with_params(*args, **kwargs):
            _format = instance.format
            if 'format' in kwargs:
                instance.format = kwargs['format']
            ret = self.function(instance, *args, **kwargs)
            instance.format = _format
            return ret
        return with_params


class ClientBase(object):
    """Client for the OpenStack Apmec v1.0 API.

    :param string username: Username for authentication. (optional)
    :param string user_id: User ID for authentication. (optional)
    :param string password: Password for authentication. (optional)
    :param string token: Token for authentication. (optional)
    :param string tenant_name: Tenant name. (optional)
    :param string tenant_id: Tenant id. (optional)
    :param string auth_strategy: 'keystone' by default, 'noauth' for no
                                 authentication against keystone. (optional)
    :param string auth_url: Keystone service endpoint for authorization.
    :param string service_type: Network service type to pull from the
                                keystone catalog (e.g. 'network') (optional)
    :param string endpoint_type: Network service endpoint type to pull from the
                                 keystone catalog (e.g. 'publicURL',
                                 'internalURL', or 'adminURL') (optional)
    :param string region_name: Name of a region to select when choosing an
                               endpoint from the service catalog.
    :param string endpoint_url: A user-supplied endpoint URL for the apmec
                            service.  Lazy-authentication is possible for API
                            service calls if endpoint is set at
                            instantiation.(optional)
    :param integer timeout: Allows customization of the timeout for client
                            http requests. (optional)
    :param bool insecure: SSL certificate validation. (optional)
    :param bool log_credentials: Allow for logging of passwords or not.
                                 Defaults to False. (optional)
    :param string ca_cert: SSL CA bundle file to use. (optional)
    :param integer retries: How many times idempotent (GET, PUT, DELETE)
                            requests to Apmec server should be retried if
                            they fail (default: 0).
    :param bool raise_errors: If True then exceptions caused by connection
                              failure are propagated to the caller.
                              (default: True)
    :param session: Keystone client auth session to use. (optional)
    :param auth: Keystone auth plugin to use. (optional)

    Example::

        from apmecclient.v1_0 import client
        apmec = client.Client(username=USER,
                                password=PASS,
                                tenant_name=TENANT_NAME,
                                auth_url=KEYSTONE_URL)

        nets = apmec.list_networks()
        ...

    """

    # API has no way to report plurals, so we have to hard code them
    # This variable should be overridden by a child class.
    EXTED_PLURALS = {}

    def __init__(self, **kwargs):
        """Initialize a new client for the Apmec v1.0 API."""
        super(ClientBase, self).__init__()
        self.retries = kwargs.pop('retries', 0)
        self.raise_errors = kwargs.pop('raise_errors', True)
        self.httpclient = client.construct_http_client(**kwargs)
        self.version = '1.0'
        self.format = 'json'
        self.action_prefix = "/v%s" % (self.version)
        self.retry_interval = 1

    def _handle_fault_response(self, status_code, response_body):
        # Create exception with HTTP status code and message
        _logger.debug("Error message: %s", response_body)
        # Add deserialized error message to exception arguments
        try:
            des_error_body = self.deserialize(response_body, status_code)
        except Exception:
            # If unable to deserialized body it is probably not a
            # Apmec error
            des_error_body = {'message': response_body}
        # Raise the appropriate exception
        exception_handler_v10(status_code, des_error_body)

    def do_request(self, method, action, body=None, headers=None, params=None):
        # Add format and tenant_id
        action += ".%s" % self.format
        action = self.action_prefix + action
        if type(params) is dict and params:
            params = utils.safe_encode_dict(params)
            action += '?' + urlparse.urlencode(params, doseq=1)

        if body:
            body = self.serialize(body)

        resp, replybody = self.httpclient.do_request(
            action, method, body=body,
            content_type=self.content_type())

        status_code = resp.status_code
        if status_code in (requests.codes.ok,
                           requests.codes.created,
                           requests.codes.accepted,
                           requests.codes.no_content):
            return self.deserialize(replybody, status_code)
        else:
            if not replybody:
                replybody = resp.reason
            self._handle_fault_response(status_code, replybody)

    def get_auth_info(self):
        return self.httpclient.get_auth_info()

    def serialize(self, data):
        """Serializes a dictionary into either XML or JSON.

        A dictionary with a single key can be passed and it can contain any
        structure.
        """
        if data is None:
            return None
        elif type(data) is dict:
            return serializer.Serializer(
                self.get_attr_metadata()).serialize(data, self.content_type())
        else:
            raise Exception(_("Unable to serialize object of type = '%s'") %
                            type(data))

    def deserialize(self, data, status_code):
        """Deserializes an XML or JSON string into a dictionary."""
        if status_code == 204:
            return data
        return serializer.Serializer(self.get_attr_metadata()).deserialize(
            data, self.content_type())['body']

    def get_attr_metadata(self):
        if self.format == 'json':
            return {}
        old_request_format = self.format
        self.format = 'json'
        exts = self.list_extensions()['extensions']
        self.format = old_request_format
        ns = dict([(ext['alias'], ext['namespace']) for ext in exts])
        self.EXTED_PLURALS.update(constants.PLURALS)
        return {'plurals': self.EXTED_PLURALS,
                'xmlns': constants.XML_NS_V10,
                constants.EXT_NS: ns}

    def content_type(self, _format=None):
        """Returns the mime-type for either 'xml' or 'json'.

        Defaults to the currently set format.
        """
        _format = _format or self.format
        return "application/%s" % (_format)

    def retry_request(self, method, action, body=None,
                      headers=None, params=None):
        """Call do_request with the default retry configuration.

        Only idempotent requests should retry failed connection attempts.
        :raises: ConnectionFailed if the maximum # of retries is exceeded
        """
        max_attempts = self.retries + 1
        for i in range(max_attempts):
            try:
                return self.do_request(method, action, body=body,
                                       headers=headers, params=params)
            except exceptions.ConnectionFailed:
                # Exception has already been logged by do_request()
                if i < self.retries:
                    _logger.debug('Retrying connection to Apmec service')
                    time.sleep(self.retry_interval)
                elif self.raise_errors:
                    raise

        if self.retries:
            msg = (_("Failed to connect to Apmec server after %d attempts")
                   % max_attempts)
        else:
            msg = _("Failed to connect Apmec server")

        raise exceptions.ConnectionFailed(reason=msg)

    def delete(self, action, body=None, headers=None, params=None):
        return self.retry_request("DELETE", action, body=body,
                                  headers=headers, params=params)

    def get(self, action, body=None, headers=None, params=None):
        return self.retry_request("GET", action, body=body,
                                  headers=headers, params=params)

    def post(self, action, body=None, headers=None, params=None):
        # Do not retry POST requests to avoid the orphan objects problem.
        return self.do_request("POST", action, body=body,
                               headers=headers, params=params)

    def put(self, action, body=None, headers=None, params=None):
        return self.retry_request("PUT", action, body=body,
                                  headers=headers, params=params)

    def list(self, collection, path, retrieve_all=True, **params):
        if retrieve_all:
            res = []
            for r in self._pagination(collection, path, **params):
                res.extend(r[collection])
            return {collection: res}
        else:
            return self._pagination(collection, path, **params)

    def _pagination(self, collection, path, **params):
        if params.get('page_reverse', False):
            linkrel = 'previous'
        else:
            linkrel = 'next'
        next = True
        while next:
            res = self.get(path, params=params)
            yield res
            next = False
            try:
                for link in res['%s_links' % collection]:
                    if link['rel'] == linkrel:
                        query_str = urlparse.urlparse(link['href']).query
                        params = urlparse.parse_qs(query_str)
                        next = True
                        break
            except KeyError:
                break


class Client(ClientBase):

    extensions_path = "/extensions"
    extension_path = "/extensions/%s"

    meads_path = '/meads'
    mead_path = '/meads/%s'
    meas_path = '/meas'
    mea_path = '/meas/%s'
    mea_scale_path = '/meas/%s/actions'
    mea_resources_path = '/meas/%s/resources'

    vims_path = '/vims'
    vim_path = '/vims/%s'

    mecads_path = '/mecads'
    mecad_path = '/mecads/%s'

    mecas_path = '/mecas'
    meca_path = '/mecas/%s'

    events_path = '/events'
    event_path = '/events/%s'

    mesds_path = '/mesds'
    mesd_path = '/mesds/%s'

    mess_path = '/mess'
    mes_path = '/mess/%s'

    # API has no way to report plurals, so we have to hard code them
    # EXTED_PLURALS = {}

    @APIParamsCall
    def list_extensions(self, **_params):
        """Fetch a list of all exts on server side."""
        return self.get(self.extensions_path, params=_params)

    @APIParamsCall
    def show_extension(self, ext_alias, **_params):
        """Fetch a list of all exts on server side."""
        return self.get(self.extension_path % ext_alias, params=_params)

    _MEAD = "mead"
    _MESD = "mesd"
    _MECAD = "mecad"

    @APIParamsCall
    def list_meads(self, retrieve_all=True, **_params):
        meads_dict = self.list(self._MEAD + 's',
                               self.meads_path,
                               retrieve_all,
                               **_params)
        for mead in meads_dict['meads']:
            if mead.get('description'):
                if len(mead['description']) > DEFAULT_DESC_LENGTH:
                    mead['description'] = \
                        mead['description'][:DEFAULT_DESC_LENGTH]
                    mead['description'] += '...'
        return meads_dict

    @APIParamsCall
    def show_mead(self, mead, **_params):
        return self.get(self.mead_path % mead,
                        params=_params)

    @APIParamsCall
    def create_mead(self, body):
        body[self._MEAD]['service_types'] = [{'service_type': 'mead'}]
        return self.post(self.meads_path, body)

    @APIParamsCall
    def delete_mead(self, mead):
        return self.delete(self.mead_path % mead)

    @APIParamsCall
    def list_meas(self, retrieve_all=True, **_params):
        meas = self.list('meas', self.meas_path, retrieve_all, **_params)
        for mea in meas['meas']:
            error_reason = mea.get('error_reason', None)
            if error_reason and \
                len(error_reason) > DEFAULT_ERROR_REASON_LENGTH:
                mea['error_reason'] = error_reason[
                    :DEFAULT_ERROR_REASON_LENGTH]
                mea['error_reason'] += '...'
        return meas

    @APIParamsCall
    def show_mea(self, mea, **_params):
        return self.get(self.mea_path % mea, params=_params)

    @APIParamsCall
    def create_mea(self, body):
        return self.post(self.meas_path, body=body)

    @APIParamsCall
    def delete_mea(self, mea):
        return self.delete(self.mea_path % mea)

    @APIParamsCall
    def update_mea(self, mea, body):
        return self.put(self.mea_path % mea, body=body)

    @APIParamsCall
    def list_mea_resources(self, mea, retrieve_all=True, **_params):
        return self.list('resources', self.mea_resources_path % mea,
                         retrieve_all, **_params)

    @APIParamsCall
    def scale_mea(self, mea, body=None):
        return self.post(self.mea_scale_path % mea, body=body)

    @APIParamsCall
    def show_vim(self, vim, **_params):
        return self.get(self.vim_path % vim, params=_params)

    _VIM = "vim"

    @APIParamsCall
    def create_vim(self, body):
        return self.post(self.vims_path, body=body)

    @APIParamsCall
    def delete_vim(self, vim):
        return self.delete(self.vim_path % vim)

    @APIParamsCall
    def update_vim(self, vim, body):
        return self.put(self.vim_path % vim, body=body)

    @APIParamsCall
    def list_vims(self, retrieve_all=True, **_params):
        return self.list('vims', self.vims_path, retrieve_all, **_params)

    @APIParamsCall
    def list_events(self, retrieve_all=True, **_params):
        events = self.list('events', self.events_path, retrieve_all,
                           **_params)
        return events

    @APIParamsCall
    def list_mea_events(self, retrieve_all=True, **_params):
        _params['resource_type'] = 'mea'
        events = self.list('events', self.events_path, retrieve_all,
                           **_params)
        mea_events = {}
        mea_events['mea_events'] = events['events']
        return mea_events

    @APIParamsCall
    def list_mead_events(self, retrieve_all=True, **_params):
        _params['resource_type'] = 'mead'
        events = self.list('events', self.events_path, retrieve_all,
                           **_params)
        mead_events = {}
        mead_events['mead_events'] = events['events']
        return mead_events

    @APIParamsCall
    def list_vim_events(self, retrieve_all=True, **_params):
        _params['resource_type'] = 'vim'
        events = self.list('events', self.events_path, retrieve_all,
                           **_params)
        vim_events = {}
        vim_events['vim_events'] = events['events']
        return vim_events

    @APIParamsCall
    def show_event(self, event_id, **_params):
        return self.get(self.event_path % event_id, params=_params)

    @APIParamsCall
    def list_mesds(self, retrieve_all=True, **_params):
        mesds_dict = self.list(self._MESD + 's',
                              self.mesds_path,
                              retrieve_all,
                              **_params)
        for mesd in mesds_dict['mesds']:
            if 'description' in mesd.keys() and \
                            len(mesd['description']) > DEFAULT_DESC_LENGTH:
                mesd['description'] = mesd['description'][:DEFAULT_DESC_LENGTH]
                mesd['description'] += '...'
        return mesds_dict

    @APIParamsCall
    def show_mesd(self, mesd, **_params):
        return self.get(self.mesd_path % mesd,
                        params=_params)

    @APIParamsCall
    def create_mesd(self, body):
        return self.post(self.mesds_path, body)

    @APIParamsCall
    def delete_mesd(self, mesd):
        return self.delete(self.mesd_path % mesd)

    @APIParamsCall
    def list_mess(self, retrieve_all=True, **_params):
        mess = self.list('mess', self.mess_path, retrieve_all, **_params)
        for mes in mess['mess']:
            error_reason = mes.get('error_reason', None)
            if error_reason and \
                            len(error_reason) > DEFAULT_ERROR_REASON_LENGTH:
                mes['error_reason'] = error_reason[
                                     :DEFAULT_ERROR_REASON_LENGTH]
                mes['error_reason'] += '...'
        return mess

    @APIParamsCall
    def show_mes(self, mes, **_params):
        return self.get(self.mes_path % mes, params=_params)

    @APIParamsCall
    def create_mes(self, body):
        return self.post(self.mess_path, body=body)

    @APIParamsCall
    def delete_mes(self, mes):
        return self.delete(self.mes_path % mes)

    @APIParamsCall
    def update_mes(self, mes, body):
        return self.put(self.mes_path % mes, body=body)

    @APIParamsCall
    def list_mecads(self, retrieve_all=True, **_params):
        mecads_dict = self.list(self._MECAD + 's',
                               self.mecads_path,
                               retrieve_all,
                               **_params)
        for mecad in mecads_dict['mecads']:
            if 'description' in mecad.keys() and \
                            len(mecad['description']) > DEFAULT_DESC_LENGTH:
                mecad['description'] = mecad['description'][:DEFAULT_DESC_LENGTH]
                mecad['description'] += '...'
        return mecads_dict

    @APIParamsCall
    def show_mecad(self, mecad, **_params):
        return self.get(self.mecad_path % mecad,
                        params=_params)

    @APIParamsCall
    def create_mecad(self, body):
        return self.post(self.mecads_path, body)

    @APIParamsCall
    def delete_mecad(self, mecad):
        return self.delete(self.mecad_path % mecad)

    @APIParamsCall
    def list_mecas(self, retrieve_all=True, **_params):
        mecas = self.list('mecas', self.mecas_path, retrieve_all, **_params)
        for meca in mecas['mecas']:
            error_reason = meca.get('error_reason', None)
            if error_reason and \
                            len(error_reason) > DEFAULT_ERROR_REASON_LENGTH:
                meca['error_reason'] = error_reason[
                                      :DEFAULT_ERROR_REASON_LENGTH]
                meca['error_reason'] += '...'
        return mecas

    @APIParamsCall
    def show_meca(self, meca, **_params):
        return self.get(self.meca_path % meca, params=_params)

    @APIParamsCall
    def create_meca(self, body):
        return self.post(self.mecas_path, body=body)

    @APIParamsCall
    def delete_meca(self, meca):
        return self.delete(self.meca_path % meca)

    @APIParamsCall
    def update_meca(self, meca, body):
        return self.put(self.meca_path % meca, body=body)
