#This file is part asterisk module for Tryton.
#The COPYRIGHT file at the top level of this repository contains
#the full copyright notices and license terms.
from trytond.model import ModelView, ModelSQL, ModelSingleton, fields, Unique
from trytond.pool import Pool
from trytond.transaction import Transaction
import logging
import socket
import unicodedata
import time
from trytond.i18n import gettext
from trytond.exceptions import UserError

__all__ = ['AsteriskConfiguration', 'AsteriskConfigurationCompany']


class AsteriskConfiguration(ModelSingleton, ModelSQL, ModelView):
    'Asterisk Configuration'
    __name__ = 'asterisk.configuration'
    name = fields.Function(fields.Char('Asterisk server name', required=True,
            help="Asterisk server name."), 'get_fields', setter='set_fields')
    ip_address = fields.Function(fields.Char('Asterisk IP addr. or DNS',
            required=True,
            help="IPv4 address or DNS name of the Asterisk server."),
        'get_fields', setter='set_fields')
    port = fields.Function(fields.Integer('Port', required=True,
            help="TCP port on which the Asterisk Manager Interface listens. "
            "Defined in /etc/asterisk/manager.conf on Asterisk."),
        'get_fields', setter='set_fields')
    out_prefix = fields.Function(fields.Char('Out prefix',
            help="Prefix to dial to place outgoing calls. If you don't use a "
            "prefix to place outgoing calls, leave empty."),
        'get_fields', setter='set_fields')
    national_prefix = fields.Function(fields.Char('National prefix',
            help="Prefix for national phone calls (don't include the 'out"
            " prefix'). For example, in France, the phone numbers looks like "
            "'01 41 98 12 42': the National prefix is '0'."),
        'get_fields', setter='set_fields')
    international_prefix = fields.Function(fields.Char('International prefix',
            help="Prefix to add to make international phone calls (don't "
            "include the 'out prefix'). For example, in France, the "
            "International prefix is '00'."),
        'get_fields', setter='set_fields')
    country_prefix = fields.Function(fields.Char('My country prefix',
            required=True,
            help="Prefix to add to make international phone calls (don't "
            "include the 'out prefix'). For example, the phone prefix for "
            "France is '33'. If the phone number to dial starts with the 'My "
            "country prefix', Tryton will remove the country prefix from "
            "the phone number and add the 'out prefix' followed by the "
            "'national prefix'. If the phone number to dial doesn't start "
            "with the 'My country prefix', Tryton will add the 'out "
            "prefix' followed by the 'international prefix'."),
        'get_fields', setter='set_fields')
    national_format_allowed = fields.Function(fields.Boolean(
            'National format allowed?',
            help="Do we allow to use click2dial on phone numbers written in "
            "national format, e.g. 01 41 98 12 42, or only in the "
            "international format, e.g. +34 1 41 98 12 42 ?"),
        'get_fields', setter='set_fields')
    login = fields.Function(fields.Char('AMI login', required=True,
            help="Login that Tryton will use to communicate with the Asterisk "
            "Manager Interface. Refer to /etc/asterisk/manager.conf on "
            "your Asterisk server."),
        'get_fields', setter='set_fields')
    password = fields.Function(fields.Char('AMI password', required=True,
            help="Password that Asterisk will use to communicate with the "
            "Asterisk Manager Interface. Refer to /etc/asterisk/manager.conf "
            "on your Asterisk server."),
        'get_fields', setter='set_fields')
    context = fields.Function(fields.Char('Dialplan context', required=True,
            help="Asterisk dialplan context from which the calls will be "
            "made. Refer to /etc/asterisk/extensions.conf on your Asterisk "
            "server."),
        'get_fields', setter='set_fields')
    wait_time = fields.Function(fields.Integer('Wait time (sec)',
            required=True,
            help="Amount of time (in seconds) Asterisk will try to reach the "
            "user's phone before hanging up."),
        'get_fields', setter='set_fields')
    extension_priority = fields.Function(fields.Integer('Extension priority',
            required=True,
            help="Priority of the extension in the Asterisk dialplan. Refer "
            "to /etc/asterisk/extensions.conf on your Asterisk server."),
        'get_fields', setter='set_fields')
    alert_info = fields.Function(fields.Char('Alert-Info SIP header',
            help="Set Alert-Info header in SIP request to user's IP Phone. If "
            "empty, the Alert-Info header will not be added. You can use "
            "it to have a special ring tone for click2dial, for example "
            "you could choose a silent ring tone."),
        'get_fields', setter='set_fields')

    @classmethod
    def get_fields(cls, configurations, names):
        res = {}
        ConfigurationCompany = Pool().get('asterisk.configuration.company')
        company_id = Transaction().context.get('company')
        conf_id = configurations[0].id
        if company_id:
            confs = ConfigurationCompany.search([
                ('company', '=', company_id),
                ], limit=1)
            for conf in confs:
                for field_name in names:
                    value = getattr(conf, field_name)
                    res[field_name] = {conf_id: value}
        else:
            raise UserError('asterisk.not_company')
        return res

    @classmethod
    def set_fields(cls, configurations, name, value):
        if value:
            ConfigurationCompany = Pool().get('asterisk.configuration.company')
            company_id = Transaction().context.get('company')
            if company_id:
                configuration = ConfigurationCompany.search([
                        ('company', '=', company_id),
                        ], limit=1)
                if not configuration:
                    ConfigurationCompany.create([{
                            'company': company_id,
                            name: value,
                    }])
                else:
                    ConfigurationCompany.write([configuration[0]], {
                            name: value
                            })

    def _only_digits(self, prefix, can_be_empty):

        prefix_to_check = getattr(self, prefix)
        if not prefix_to_check:
            if not can_be_empty:
                raise UserError(gettext(prefix))
        else:
            if not prefix_to_check.isdigit():
                raise UserError(gettext(prefix))

    def _only_digits_out_prefix(self):
        return self._only_digits('out_prefix', True)

    def _only_digits_country_prefix(self):
        return self._only_digits('country_prefix', False)

    def _only_digits_national_prefix(self):
        return self._only_digits('national_prefix', True)

    def _only_digits_international_prefix(self):
        return self._only_digits('international_prefix', False)

    def _check_wait_time(self):
        if self.wait_time < 1 or self.wait_time > 120:
            raise UserError(gettext('asterisk.wait_time'))

    def _check_extension_priority(self):
        if self.extension_priority < 1:
            raise UserError(gettext('asterisk.extension_priority'))

    def _check_port(self):
        if int(self.port) > 65535 or self.port < 1:
            raise UserError(gettext('asterisk.port'))

    def validate(cls, records):
        for record in records:
            record._only_digits_out_prefix()
            record._only_digits_country_prefix()
            record._only_digits_national_prefix()
            record._only_digits_international_prefix()
            record._check_wait_time()
            record._check_extension_priority()
            record._check_port()

    @staticmethod
    def default_port():
        return 5038

    @staticmethod
    def default_out_prefix():
        return '0'

    @staticmethod
    def default_national_prefix():
        return '0'

    @staticmethod
    def default_international_prefix():
        return '00'

    @staticmethod
    def default_extension_priority():
        return 1

    @staticmethod
    def default_wait_time():
        return 5

    @staticmethod
    def unaccent(text):
        return unicodedata.normalize('NFKD', text).encode('ASCII',
            'ignore')

    @classmethod
    def reformat_number(cls, tryton_number, ast_server):
        '''
        This method transforms the number available in Tryton to the number
        that Asterisk should dial.
        '''
        logger = logging.getLogger('asterisk')

        # Let's call the variable tmp_number now
        tmp_number = tryton_number
        logger.debug('Number before reformat = %s' % tmp_number)

        # Check if empty
        if not tmp_number:
            raise UserError(gettext('asterisk.invalid_phone'),
                gettext('asterisk.invalid_format'))

        # First, we remove all stupid characters and spaces
        for i in [' ', '.', '(', ')', '[', ']', '-', '/']:
            tmp_number = tmp_number.replace(i, '')

        # Before starting to use prefix, we convert empty prefix whose value
        # is False to an empty string
        country_prefix = (ast_server.country_prefix or '')
        national_prefix = (ast_server.national_prefix or '')
        international_prefix = (ast_server.international_prefix or '')
        out_prefix = (ast_server.out_prefix or '')

        # International format
        if tmp_number[0] == '+':
            # Remove the starting '+' of the number
            tmp_number = tmp_number.replace('+', '')
            logger.debug('Number after removal of special char = %s' %
                tmp_number)

            # At this stage, 'tmp_number' should only contain digits
            if not tmp_number.isdigit():
                raise UserError(gettext('asterisk.invalid_phone'),
                    gettext('asterisk.invalid_format_msg'))

            logger.debug('Country prefix = ' + country_prefix)
            if country_prefix == tmp_number[0:len(country_prefix)]:
                # If the number is a national number,
                # remove 'my country prefix' and add 'national prefix'
                tmp_number = (national_prefix) + tmp_number[
                    len(country_prefix):len(tmp_number)]
                logger.debug('National prefix = %s - Number with national '
                    'prefix = %s' % (national_prefix, tmp_number))
            else:
                # If the number is an international number,
                # add 'international prefix'
                tmp_number = international_prefix + tmp_number
                logger.debug('International prefix = %s - Number with '
                    'international prefix = %s' % (international_prefix,
                        tmp_number))
        # National format, allowed
        elif ast_server.national_format_allowed:
            # No treatment required
            if not tmp_number.isdigit():
                raise UserError(gettext('asterisk.invalid_phone'),
                    gettext('asterisk.invalid_national_format'))

        # National format, disallowed
        elif not ast_server.national_format_allowed:
            raise UserError(gettext('asterisk.invalid_phone'),
                gettext('asterisk.invalid_international_format'))
        # Add 'out prefix' to all numbers
        tmp_number = out_prefix + tmp_number
        logger.debug('Out prefix = %s - Number to be sent to Asterisk = %s' %
            (out_prefix, tmp_number))
        return tmp_number

    @classmethod
    def dial(cls, party, tryton_number):
        '''
        Open the socket to the Asterisk Manager Interface (AMI)
        and send instructions to Dial to Asterisk.
        '''
        logger = logging.getLogger('asterisk')
        User = Pool().get('res.user')
        user_id = Transaction().user
        if user_id == 0 and 'user' in Transaction().context:
            user_id = Transaction().context['user']
        user = User(user_id)

        # Check if the number to dial is not empty
        if not tryton_number:
            raise UserError(gettext('asterisk.error'),
                gettext('asterisk.no_phone_number'))

        # We check if the user has an Asterisk server configured
        if not user.asterisk_server:
            raise UserError(gettext('asterisk.error'),
                gettext('asterisk.no_asterisk_configuration'))
        else:
            ast_server = user.asterisk_server

        # We check if the current user has a chan type
        if not user.asterisk_chan_type:
            raise UserError(gettext('asterisk.error'),
                gettext('asterisk.no_channel_type'))

        # We check if the current user has an internal number
        if not user.internal_number:
            raise UserError(gettext('asterisk.error'),
                gettext('asterisk.no_internal_phone'))
        internal_numbers = user.internal_number.replace(" ", "").split(",")

        # The user should also have a CallerID, but in Spain that will
        # be the name of the address that we call.
        if not user.callerid:
            #Party = Pool().get('party.party')
            #callerid = Party.search(party).get_name_for_display
            callerid = party.display_name
        else:
            callerid = user.CallerId

        # Convert the phone number in the format that will be sent to Asterisk
        ast_number = cls.reformat_number(tryton_number, ast_server)
        logger.info('User dialing: channel(s) = %s/%s - Callerid = %s' %
            (user.asterisk_chan_type, internal_numbers, user.callerid))
        logger.info('Asterisk server = %s:%s' %
            (ast_server.ip_address, ast_server.port))

        # Connect to the Asterisk Manager Interface, using IPv6-ready code
        try:
            res = socket.getaddrinfo(ast_server.ip_address, ast_server.port,
                socket.AF_UNSPEC, socket.SOCK_STREAM)
        except:
            logger.error("Can't resolve the DNS of the Asterisk server : %s" %
                str(ast_server.ip_address))
            raise UserError(gettext('asterisk.error'),
                gettext('asterisk.cant_resolve_dns'))
        for result in res:
            af, socktype, proto, _, sockaddr = result
            for internal_number in internal_numbers:
                try:
                    sock = socket.socket(af, socktype, proto)
                    sock.connect(sockaddr)
                    sock.send('Action: login\r\n')
                    sock.send('Events: off\r\n')
                    sock.send('Username: %s\r\n' % str(ast_server.login))
                    sock.send('Secret: %s\r\n\r\n' % str(ast_server.password))
                    time.sleep(1)
                    response_login = sock.recv(1024)
                    sock.send('Action: originate\r\n')
                    sock.send('Channel: %s/%s\r\n' % (
                            str(user.asterisk_chan_type),
                            str(internal_number)))
                    sock.send('Timeout: %s\r\n' % str(ast_server.wait_time*1000))
                    sock.send('CallerId: %s\r\n' % cls.unaccent(callerid))
                    sock.send('Exten: %s\r\n' % str(ast_number))
                    sock.send('Context: %s\r\n' % str(ast_server.context))
                    if (ast_server.alert_info and
                            user.asterisk_chan_type == 'SIP'):
                        sock.send('Variable: SIPAddHeader=Alert-Info: %s\r\n' %
                            str(ast_server.alert_info))
                    sock.send('Priority: %s\r\n\r\n' %
                        str(ast_server.extension_priority))
                    time.sleep(1)
                    response_originate = sock.recv(1024)
                    sock.send('Action: Logoff\r\n\r\n')
                    response_logoff = sock.recv(1024)
                    sock.close()
                    if "Success" in response_originate:
                        logger.info("Asterisk Click2Dial from %s to %s "
                            "success" % (internal_number, ast_number))
                        break
                    else:
                        logger.info("Asterisk Click2Dial from %s to %s failed:"
                            "\n%s" % (internal_number, ast_number,
                                response_originate))
                except:
                    logger.debug("Asterisk Click2dial failed: unable to "
                        "connect to Asterisk server")
                    raise UserError(gettext('asterisk.error'),
                        gettext('asterisk.connection_failed'))


class AsteriskConfigurationCompany(ModelSQL, ModelView):
    'Asterisk Configuration Company'
    __name__ = 'asterisk.configuration.company'

    company = fields.Many2One('company.company', 'Company', readonly=True)
    name = fields.Char('Asterisk server name')
    ip_address = fields.Char('Asterisk IP addr. or DNS')
    port = fields.Integer('Port')
    out_prefix = fields.Char('Out prefix')
    national_prefix = fields.Char('National prefix')
    international_prefix = fields.Char('International prefix')
    country_prefix = fields.Char('My country prefix')
    national_format_allowed = fields.Boolean('National format allowed?')
    login = fields.Char('AMI login')
    #TODO: Make not visible the password
    password = fields.Char('AMI password')
    context = fields.Char('Dialplan context')
    wait_time = fields.Integer('Wait time (sec)')
    extension_priority = fields.Integer('Extension priority')
    alert_info = fields.Char('Alert-Info SIP header')

    @classmethod
    def __setup__(cls):
        super(AsteriskConfigurationCompany, cls).__setup__()
        t = cls.__table__()
        cls._sql_constraints += [
            ('company_uniq', Unique(t, t.company),
                'There is already one configuration for this company.'),
            ]
