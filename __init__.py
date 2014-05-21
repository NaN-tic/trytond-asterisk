#This file is part asterisk module for Tryton.
#The COPYRIGHT file at the top level of this repository contains
#the full copyright notices and license terms.
from trytond.pool import Pool
from .asterisk import *
from .party import *
from .user import *

def register():
    Pool.register(
        AsteriskConfiguration,
        AsteriskConfigurationCompany,
        Party,
        User,
        module='asterisk', type_='model')
