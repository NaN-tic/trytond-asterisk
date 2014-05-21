#This file is part asterisk module for Tryton.
#The COPYRIGHT file at the top level of this repository contains
#the full copyright notices and license terms.
from trytond.model import ModelView, ModelSQL, ModelSingleton, fields
from trytond.pool import Pool
from trytond.transaction import Transaction
import logging
import socket
import unicodedata

__all__ = [ 'AsteriskConfiguration', 'AsteriskConfigurationCompany']


class AsteriskConfiguration(ModelSingleton, ModelSQL, ModelView):
    'Asterisk Configuration'
    __name__ = 'asterisk.configuration'
    name = fields.Function(fields.Char('Asterisk server name', required=True,
            help="Asterisk server name."), 'get_fields', setter='set_fields')
    ip_address = fields.Function(fields.Char('Asterisk IP addr. or DNS',
            required=True,
            help="IPv4 address or DNS name of the Asterisk server."),
        'get_fields', setter='set_fields')
    port = fields.Function(fields.Char('Port', required=True,
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
        prefix_to_check = self.read([self.id], [prefix])[0]
        if prefix_to_check:
            prefix_to_check = prefix_to_check[prefix]
        if not prefix_to_check:
            if not can_be_empty:
                return False
        else:
            if not prefix_to_check.isdigit():
                return False
        return True

    def _only_digits_port(self):
        return self._only_digits('port', False)

    def _only_digits_out_prefix(self):
        return self._only_digits('out_prefix', True)

    def _only_digits_country_prefix(self):
        return self._only_digits('country_prefix', False)

    def _only_digits_national_prefix(self):
        return self._only_digits('national_prefix', True)

    def _only_digits_international_prefix(self):
        return self._only_digits('international_prefix', False)

    def _check_wait_time(self):
        wait_time_to_check = self.read([self.id], ['wait_time'])[0]\
            ['wait_time']
        if wait_time_to_check < 1 or wait_time_to_check > 120:
            return False
        return True

    def _check_extension_priority(self):
        extension_priority_to_check = self.read([self.id],
            ['extension_priority'])[0]['extension_priority']
        if extension_priority_to_check < 1:
            return False
        return True

    def _check_port(self):
        port_to_check = self.read([self.id], ['port'])[0]['port']
        if int(port_to_check) > 65535 or int(port_to_check) < 1:
            return False
        return True

    @classmethod
    def __setup__(cls):
        super(AsteriskConfiguration, cls).__setup__()
        cls._constraints += [
            ('_only_digits_port', 'port'),
            ('_only_digits_out_prefix', 'out_prefix'),
            ('_only_digits_country_prefix', 'country_prefix'),
            ('_only_digits_national_prefix', 'national_prefix'),
            ('_only_digits_international_prefix', 'international_prefix'),
            ('_check_wait_time', 'wait_time'),
            ('_check_extension_priority', 'extension_priority'),
            ('_check_port', 'port'),
        ]
        cls._error_messages.update({
                'out_prefix': "Use only digits for the 'Out prefix' or leave "
                "it empty.",
                'country_prefix': "Use only digits for the 'Country prefix'.",
                'national_prefix': "Use only digits for the 'National prefix' "
                "or leave it empty.",
                'international_prefix': "Use only digits for 'International "
                "prefix'.",
                'wait_time': "You should enter a 'Wait time' value between 1 "
                "and 120 seconds.",
                'extension_priority': "The 'Extension priority' must be a "
                "positive value.",
                'port': 'TCP ports range from 1 to 65535.',
                'error': 'Error',
                'invalid_phone': 'Invalid phone number',
                'invalid_international_format': "The phone number is not "
                "written in a valid international format. Example of valid "
                "international format: +33 1 41 98 12 42.",
                'invalid_national_format': "The phone number is not written "
                "in a valid national format.",
                'invalid_format': "The phone number is not written in a valid "
                "format.",
                'no_phone_number': "There is no phone number.",
                'no_asterisk_configuration': "Not available Asterisk Server "
                "configured for the current user.",
                'no_channel_type': "There isn't a channel type configured for "
                "the current user",
                'no_internal_phone': "There isn't a internal phone number "
                "configured for the current user",
                'cant_resolve_dns': "Can't resolve the DNS of the Asterisk "
                "server:",
                'connection_failed': "The connection from Tryton to the "
                "Asterisk server has failed. Please check the configuration "
                "on Tryton and Asterisk.",
                })

    @staticmethod
    def default_port():
        return '5038'

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
        if isinstance(text, str):
            text = unicode(text, 'utf-8')
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
            cls.raise_user_error(error='invalid_phone',
                error_description='invalid_format')

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
            tmp_number = tmp_number.replace('+','')
            logger.debug('Number after removal of special char = %s' % \
                tmp_number)

            # At this stage, 'tmp_number' should only contain digits
            if not tmp_number.isdigit():
                cls.raise_user_error(error='invalid_phone',
                    error_description='invalid_format_msg')

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
                cls.raise_user_error(error='invalid_phone',
                    error_description='invalid_national_format')

        # National format, disallowed
        elif not ast_server.national_format_allowed:
            cls.raise_user_error(error='invalid_phone',
                error_description='invalid_international_format')
        # Add 'out prefix' to all numbers
        tmp_number = out_prefix + tmp_number
        logger.debug('Out prefix = %s - Number to be sent to Asterisk = %s' % \
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
            cls.raise_user_error(error='error',
                error_description='no_phone_number')

        # We check if the user has an Asterisk server configured
        if not user.asterisk_server:
            cls.raise_user_error(error='error',
                error_description='no_asterisk_configuration')
        else:
            ast_server = user.asterisk_server

        # We check if the current user has a chan type
        if not user.asterisk_chan_type:
            cls.raise_user_error(error='error',
                error_description='no_channel_type')

        # We check if the current user has an internal number
        if not user.internal_number:
            cls.raise_user_error(error='error',
                error_description='no_internal_phone')

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
        logger.info('User dialing: channel = %s/%s - Callerid = %s' % \
            (user.asterisk_chan_type, user.internal_number, user.callerid))
        logger.info('Asterisk server = %s:%s' % \
            (ast_server.ip_address, ast_server.port))

        # Connect to the Asterisk Manager Interface, using IPv6-ready code
        try:
            res = socket.getaddrinfo(ast_server.ip_address, ast_server.port,
                socket.AF_UNSPEC, socket.SOCK_STREAM)
        except:
            logger.error("Can't resolve the DNS of the Asterisk server : %s" %\
                str(ast_server.ip_address))
            cls.raise_user_error(error='error',
                error_description='cant_resolve_dns')
        for result in res:
            af, socktype, proto, _, sockaddr = result
            try:
                sock = socket.socket(af, socktype, proto)
                sock.connect(sockaddr)
                sock.send('Action: login\r\n')
                sock.send('Events: off\r\n')
                sock.send('Username: %s\r\n' % str(ast_server.login))
                sock.send('Secret: %s\r\n\r\n' % str(ast_server.password))
                sock.send('Action: originate\r\n')
                sock.send('Channel: %s/%s\r\n' % (str(user.asterisk_chan_type),
                    str(user.internal_number)))
                sock.send('Timeout: %s\r\n' % str(ast_server.wait_time*1000))
                sock.send('CallerId: %s\r\n' % cls.unaccent(callerid))
                sock.send('Exten: %s\r\n' % str(ast_number))
                sock.send('Context: %s\r\n' % str(ast_server.context))
                if ast_server.alert_info and user.asterisk_chan_type == 'SIP':
                    sock.send('Variable: SIPAddHeader=Alert-Info: %s\r\n' % \
                        str(ast_server.alert_info))
                sock.send('Priority: %s\r\n\r\n' % \
                    str(ast_server.extension_priority))
                sock.send('Action: Logoff\r\n\r\n')
                sock.close()
            except:
                logger.debug("Click2dial failed: unable to connect to "
                    "Asterisk")
                cls.raise_user_error(error='error',
                    error_description='connection_failed')
            logger.info("Asterisk Click2Dial from %s to %s" % \
                (user.internal_number, ast_number))


class AsteriskConfigurationCompany(ModelSQL, ModelView):
    'Asterisk Configuration Company'
    __name__ = 'asterisk.configuration.company'

    company = fields.Many2One('company.company', 'Company', readonly=True)
    name = fields.Char('Asterisk server name')
    ip_address = fields.Char('Asterisk IP addr. or DNS')
    port = fields.Char('Port')
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
        cls._sql_constraints += [
            ('company_uniq', 'UNIQUE(company)',
                'There is already one configuration for this company.'),
            ]
