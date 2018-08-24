#This file is part asterisk module for Tryton.
#The COPYRIGHT file at the top level of this repository contains
#the full copyright notices and license terms.
from trytond.pool import PoolMeta

__all__ = ['Party']


class Party(metaclass=PoolMeta):
    __name__ = 'party.party'

    @property
    def display_name(self):
        return self.trade_name or self.name or "UNKNOWN NAME"
