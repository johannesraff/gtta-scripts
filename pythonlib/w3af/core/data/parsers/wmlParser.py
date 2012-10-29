'''
wmlParser.py

Copyright 2006 Andres Riancho

This file is part of w3af, w3af.sourceforge.net .

w3af is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation version 2 of the License.

w3af is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with w3af; if not, write to the Free Software
Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

'''

import core.controllers.outputManager as om

from core.data.parsers.sgmlParser import SGMLParser
from core.data.parsers.urlParser import url_object

import core.data.dc.form as form


class wmlParser(SGMLParser):
    '''
    This class is a WML parser. WML is used in cellphone "web" pages.
    
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    
    def __init__(self, httpResponse):
        self._select_tag_name = ""
        SGMLParser.__init__(self, httpResponse)
        
    def _pre_parse(self, httpResponse):
        '''
        @parameter httpResponse: The HTTP response document that contains the WML
        document inside its body.

        Init,
        >>> from core.data.url.httpResponse import httpResponse as httpResponse
        >>> u = url_object('http://www.w3af.com/')
        
        Parse a simple form,
        >>> form = """
        ...    <go method="post" href="dataReceptor.php">
        ...        <postfield name="clave" value="$(clave)"/>
        ...        <postfield name="cuenta" value="$(cuenta)"/>
        ...        <postfield name="tipdat" value="D"/>
        ...    </go>"""
        >>> response = httpResponse( 200, form, {}, u, u )
        >>> w = wmlParser(response)
        >>> w.getForms()
        [{'tipdat': ['D'], 'clave': ['$(clave)'], 'cuenta': ['$(cuenta)']}]

        Get the simplest link
        >>> response = httpResponse( 200, '<a href="/index.aspx">ASP.NET</a>', {}, u, u )
        >>> w = wmlParser( response )
        >>> re, parsed = w.getReferences()
        
        #
        #    TODO:
        #        I don't really understand why I'm getting results @ the "re".
        #        They should really be inside the "parsed" list.
        #
        #    >>> re
        #    []
        #    >>> parsed[0].url_string
        #    u'http://www.w3af.com/index.aspx'

        Get a link by applying regular expressions
        >>> response = httpResponse(200, 'header /index.aspx footer', {}, u, u)
        >>> w = wmlParser( response )
        >>> re, parsed = w.getReferences()
        >>> #
        >>> # TODO: Shouldn't this be the other way around?!
        >>> #
        >>> re
        []
        >>> parsed[0].url_string
        u'http://www.w3af.com/index.aspx'
        '''
        SGMLParser._pre_parse(self, httpResponse)
        assert self._baseUrl is not None, 'The base URL must be set.'
    
    def _handle_go_tag_start(self, tag, attrs):
        
        # Find method
        method = attrs.get('method', 'GET').upper()
        
        # Find action
        action = attrs.get('href', '')
        if action:
            self._inside_form = True
            action = unicode(self._baseUrl.urlJoin(action))
            action = url_object(self._decode_URL(action),
                                encoding=self._encoding)
            # Create the form
            f = form.form(encoding=self._encoding)
            f.setMethod(method)           
            f.setAction(action)
            self._forms.append(f)
        else:
            om.out.debug('wmlParser found a form without an action. '
                         'Javascript is being used.')
    
    def _handle_go_tag_end(self, tag):
        self._inside_form = False
    
    def _handle_input_tag_start(self, tag, attrs):
        if self._inside_form:
            # We are working with the last form
            f = self._forms[-1]
            f.addInput(attrs.items())
    
    _handle_postfield_tag_start = \
                            _handle_setvar_tag_start = _handle_input_tag_start
    
    def _handle_select_tag_start(self, tag, attrs):
        if self._inside_form:
            self._select_tag_name = select_name = attrs.get('name', '') or \
                                                    attrs.get('id', '')
            if select_name:
                self._inside_select = True
            else:
                om.out.debug('wmlParser found a select tag without a '
                             'name attr !')
                self._inside_select = False
    
    def _handle_option_tag_start(self, tag, attrs):
        if self._inside_form and self._inside_select:
            # Working with the last form in the list
            f = self._forms[-1]
            attrs['name'] = self._select_tag_name 
            f.addInput(attrs.items())
    