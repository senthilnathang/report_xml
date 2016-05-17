# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#
#    Copyright (c) 2014 Noviat nv/sa (www.noviat.com). All rights reserved.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from lxml import etree
import xml.dom.minidom as minidom
import openerp
import openerp.tools as tools
from openerp.tools.safe_eval import safe_eval
from openerp.report import print_fnc
from datetime import datetime
from openerp.osv.fields import datetime as datetime_field
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
import inspect
from types import CodeType
from openerp.report.report_sxw import *
from openerp import pooler
from openerp.tools.translate import translate, _
import logging
_logger = logging.getLogger(__name__)


class AttrDict(dict):
    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self


class report_xml(report_sxw):

    def prettify_xml_etree(self,obj):
        return etree.tostring(obj,encoding="utf-8",xml_declaration=True,pretty_print=True)

    def pretty_xml(self,obj):
        return obj.toprettyxml(indent="    ",encoding="utf-8")

    def generate_xml_report(self, parser, data, objects,context=None):
        """ override this method to create your xml file """
        raise NotImplementedError()

    def parsestring(self,obj):
        return etree.tostring(obj)

    def close(self):
        self.doc = None
        self.dom = None


    def create(self, cr, uid, ids, data, context=None):
        self.pool = pooler.get_pool(cr.dbname)
        self.cr = cr
        self.uid = uid
        report_obj = self.pool.get('ir.actions.report.xml')
        report_ids = report_obj.search(cr, uid,
                [('report_name', '=', self.name[7:])], context=context)
        if report_ids:
            report_xml = report_obj.browse(cr, uid, report_ids[0], context=context)
            self.title = report_xml.name
            if report_xml.report_type == 'xml':
                return self.create_source_xml(cr, uid, ids, data, context)
        elif context.get('xml_export'):
            self.table = data.get('model') or self.table   # use model from 'data' when no ir.actions.report.xml entry
            return self.create_source_xml(cr, uid, ids, data, context)
        return super(report_xml, self).create(cr, uid, ids, data, context)

    def minidom(self,obj):
        """Parse using MiniDOM"""
        #Parse String
        string = self.parsestring(obj)
        #Reprase Before Prettify
        reparsed = minidom.parseString(string)
        #Pretty XML
        xml_value = self.pretty_xml(reparsed)
        return xml_value

    def create_source_xml(self, cr, uid, ids, data, context=None):
        if not context:
            context = {}
        parser_instance = self.parser(cr, uid, self.name2, context)
        self.parser_instance = parser_instance
        self.context = context
        objs = self.getObjects(cr, uid, ids, context)
        parser_instance.set_context(objs, data, ids, 'xml')
        objs = parser_instance.localcontext['objects']
        _p = AttrDict(parser_instance.localcontext)
        #_p is the Parser
        obj,xml_parser=self.generate_xml_report(_p, data, objs,context=context)
        if xml_parser == 'minidom':
            #minodom can be used instead of etree
            xml_value = self.minidom(obj)
        elif xml_parser == 'etree':
            #prettify_xml using etree
            xml_value = self.prettify_xml_etree(obj)
        return (xml_value, 'xml')

    def render(self,data):
        """
        returns 'evaluated' data
        """
        return data



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
