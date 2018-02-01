# This file is part asterisk module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.pool import Pool
from . import asterisk
from . import party
from . import user


def register():
    Pool.register(
        asterisk.AsteriskConfiguration,
        asterisk.AsteriskConfigurationCompany,
        party.Party,
        user.User,
        module='asterisk', type_='model')
