'''
fuzzableRequest.py

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
from urllib import unquote
import copy

from core.data.constants.encodings import DEFAULT_ENCODING
from core.controllers.w3afException import w3afException
from core.data.dc.cookie import cookie as cookie
from core.data.dc.dataContainer import dataContainer
from core.data.parsers.urlParser import url_object
import core.controllers.outputManager as om

#CR = '\r'
CR = ''
LF = '\n'
CRLF = CR + LF
SP = ' '


class fuzzableRequest(object):
    '''
    This class represents a fuzzable request. Fuzzable requests were created
    to allow w3af plugins to be much simpler and don't really care if the
    vulnerability is in the postdata, querystring, header, cookie or any other
    variable.
    
    Other classes should inherit from this one and change the behaviour of
    getURL() and getData(). For example: the class httpQsRequest should return
    the _dc in the querystring (getURL) and httpPostDataRequest should return
    the _dc in the POSTDATA (getData()).
    
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self):
        
        # Internal variables
        self._url = None
        self._uri = None
        self._method = 'GET'
        self._data = ''
        self._headers = {}
        self._cookie = None
        self._dc = dataContainer()

        # Set the internal variables
        self._sent_info_comp = None
    
    def dump( self ):
        '''
        @return: a DETAILED str representation of this fuzzable request.

        >>> fr = fuzzableRequest()
        >>> u = url_object("http://www.w3af.com/")
        >>> fr.setURL( u )
        >>> fr.dump()
        'GET http://www.w3af.com/ HTTP/1.1\\n\\n'

        >>> fr.setHeaders( {'Host':'www.w3af.com'} )
        >>> fr.dump()
        'GET http://www.w3af.com/ HTTP/1.1\\nHost: www.w3af.com\\n\\n'

        >>> fr.setHeaders( {'Host':'www.w3af.com'} )
        >>> fr.setMethod('POST')
        >>> fr.setData('D474')
        >>> fr.dump()
        'POST http://www.w3af.com/ HTTP/1.1\\nHost: www.w3af.com\\n\\nD474'
        '''
        return "%s%s%s" % (self.dumpRequestHead(),
                           CRLF, str(self.getData() or ''))
    
    def getRequestLine(self):
        '''Return request line.'''
        return "%s %s HTTP/1.1%s" % (self.getMethod(), self.getURI(), CRLF)

    def dumpRequestHead(self):
        '''
        @return: A string with the head of the request
        '''
        return "%s%s" % (self.getRequestLine(), self.dumpHeaders())
    
    def dumpHeaders( self ):
        '''
        @return: A string representation of the headers.
        '''
        return ''.join("%s: %s%s" % (h, v, CRLF) for h, v
                       in self._headers.iteritems())

    def export( self ):
        '''
        Generic version of how they are exported:
            METHOD,URL,DC
    
        Example:
            GET,http://localhost/index.php?abc=123&def=789,
            POST,http://localhost/index.php,abc=123&def=789
        
        @return: a csv str representation of the request

        >>> from core.data.dc.dataContainer import dataContainer
        >>> fr = fuzzableRequest()
        >>> u = url_object("""http://www.w3af.com/""")
        >>> fr.setURL( u )
        >>> fr.export()
        'GET,http://www.w3af.com/,'

        >>> fr = fuzzableRequest()
        >>> u = url_object("""http://www.w3af.com/""")
        >>> d = dataContainer()
        >>> d['a'] = ['1',]
        >>> fr.setURL( u )
        >>> fr.setDc( d )
        >>> fr.export()
        'GET,http://www.w3af.com/?a=1,'

        '''
        #
        # FIXME: What if a comma is inside the URL or DC?
        # TODO: Why don't we export headers and cookies?
        #
        meth = self._method
        str_res = [meth, ',', str(self._url)]

        if meth == 'GET': 
            if self._dc:
                str_res.extend(('?', str(self._dc)))
            str_res.append(',')
        else:
            str_res.append(',')
            if self._dc:
                str_res.append(str(self._dc))
        
        return ''.join(str_res)
                    
    def sent(self, smth_instng):
        '''
        Checks if something similar to `smth_instng` was sent in the request.
        This is used to remove false positives, e.g. if a grep plugin finds a "strange"
        string and wants to be sure it was not generated by an audit plugin.
        
        This method should only be used by grep plugins which often have false
        positives.
        
        The following example shows that we sent d'z"0 but d\'z"0 will
        as well be recognised as sent

        TODO: This function is called MANY times, and under some circumstances it's
        performance REALLY matters. We need to review this function.
        
        >>> f = fuzzableRequest()
        >>> f._uri = url_object("""http://example.com/a?p=d'z"0&paged=2""")
        >>> f.sent('d%5C%27z%5C%220')
        True
        >>> f._data = 'p=<SCrIPT>alert("bsMs")</SCrIPT>'
        >>> f.sent('<SCrIPT>alert(\"bsMs\")</SCrIPT>')
        True
        >>> f = fuzzableRequest()
        >>> f._uri = url_object('http://example.com/?p=<ScRIPT>a=/PlaO/%0Afake_alert(a.source)</SCRiPT>')
        >>> f.sent('<ScRIPT>a=/PlaO/fake_alert(a.source)</SCRiPT>')
        True

        @parameter smth_instng: The string
        @return: True if something similar was sent
        '''
        def make_comp(heterogen_string):
            '''
            This basically removes characters that are hard to compare
            '''
            heterogen_characters = ('\\', '\'', '"', '+',' ', chr(0), 
                                    chr(int("0D",16)), chr(int("0A",16)))
            #heterogen_characters.extend(string.whitespace)

            for hetero_char in heterogen_characters:
                heterogen_string = heterogen_string.replace(hetero_char, '')
            return heterogen_string
        
        # This is the easy part. If it was exactly like this in the request
        if smth_instng in self._data or \
            smth_instng in self.getURI() or \
            smth_instng in unquote(self._data) or \
            smth_instng in unicode(self._uri.urlDecode()):
            return True
        
        # Ok, it's not in it but maybe something similar
        # Let's set up something we can compare
        if self._sent_info_comp is None:
            dc = self._dc
            dec_dc = unquote(str(dc)).decode(dc.encoding)
            data = '%s%s%s' % (unicode(self._uri), self._data, dec_dc)
            
            self._sent_info_comp = make_comp(data + unquote(data))
        
        minLength = 3
        # make the smth_instng comparable
        smth_instng_comps = (make_comp(smth_instng),
                             make_comp(unquote(smth_instng)))
        for smth_intstng_comp in smth_instng_comps:
            # We don't want false negatives just because the string is 
            # short after making comparable
            if smth_intstng_comp in self._sent_info_comp and \
                len(smth_intstng_comp) >= minLength:
                return True
        # I didn't sent the smth_instng in any way
        return False

    def __str__(self):
        '''
        @return: A string representation of this fuzzable request.

        >>> fr = fuzzableRequest()
        >>> u = url_object("""http://www.w3af.com/""")
        >>> fr.setURL( u )
        >>> str( fr )
        'http://www.w3af.com/ | Method: GET'

        >>> repr( fr )
        '<fuzzable request | GET | http://www.w3af.com/>'

        '''        
        result_string = ''
        result_string += self._url
        result_string += ' | Method: ' + self._method
        
        if self._dc:
            result_string += ' | Parameters: ('
            
            # Mangle the value for printing
            for param_name, values in self._dc.items():

                #
                # Because of repeated parameter names, we need to add this:
                #
                for the_value in values:
                    # the_value is always a string
                    if len(the_value) > 10:
                        the_value = the_value[:10] + '...'
                    the_value = '"' + the_value + '"'
                    
                    result_string += param_name + '=' + the_value + ', '
                    
            result_string = result_string[: -2]
            result_string += ')'
        
        return result_string.encode(DEFAULT_ENCODING)
    
    def __repr__( self ):
        return '<fuzzable request | %s | %s>' % \
                                        (self.getMethod(), self.getURI())
        
    def __eq__(self, other):
        '''
        Two requests are equal if:
            - They have the same URL
            - They have the same method
            - They have the same parameters
            - The values for each parameter is equal
        
        @return: True if the requests are equal.


        >>> u = url_object("""http://www.w3af.com/""")
        >>> fr1 = fuzzableRequest()
        >>> fr2 = fuzzableRequest()
        >>> fr1.setURL( u )
        >>> fr2.setURL( u )
        >>> fr1 == fr2
        True

        >>> u1 = url_object("""http://www.w3af.com/a""")
        >>> u2 = url_object("""http://www.w3af.com/b""")
        >>> fr1 = fuzzableRequest()
        >>> fr2 = fuzzableRequest()
        >>> fr1.setURL( u1 )
        >>> fr2.setURL( u2 )
        >>> fr1 == fr2
        False

        >>> u = url_object("""http://www.w3af.com/""")
        >>> fr1 = fuzzableRequest()
        >>> fr2 = fuzzableRequest()
        >>> fr1.setMethod( 'POST' )
        >>> fr1.setURL( u )
        >>> fr2.setURL( u )
        >>> fr1 == fr2
        False

        '''
        if self._uri == other._uri and \
            self._method == other._method and \
            self._dc == other._dc:
            return True
        else:
            return False
    
    def __ne__(self, other):
        return not self.__eq__(other)
            
    def is_variant_of(self, other):
        '''
        Two requests are loosely equal (or variants) if:
            - They have the same URL
            - They have the same HTTP method
            - They have the same parameter names
            - The values for each parameter have the same type (int / string)
            
        @return: True if self and other are variants.
        '''
        if self._uri == other._uri and \
           self._method == other._method and \
           self._dc.keys() == other._dc.keys():
                
            # Ok, so it has the same URI, method, dc:
            # I need to work now :(
            
            # What I do now, is check if the values for each parameter has the
            # same type or not.
            for param_name in self._dc:
                
                # repeated parameter names
                for index in xrange(len(self._dc[param_name])):
                    try:
                        # I do it in a try, because "other" might not have
                        # that many repeated parameters, and index could be
                        # out of bounds.
                        value_self = self._dc[param_name][index]
                        value_other = other._dc[param_name][index]
                    except IndexError:
                        return False
                    else:
                        if value_other.isdigit() and not value_self.isdigit():
                            return False
                        elif value_self.isdigit() and not value_other.isdigit():
                            return False

            return True
        else:
            return False
    
    def setURL( self , url ):
        if not isinstance(url, url_object):
            msg = 'The "url" parameter of setURL @ fuzzableRequest'
            msg += ' must be of urlParser.url_object type.'
            raise ValueError( msg )

        self._url = url_object( url.url_string.replace(' ', '%20') )
        self._uri = self._url
    
    def setURI( self, uri ):
        if not isinstance(uri, url_object):
            msg = 'The "url" parameter of setURL @ fuzzableRequest'
            msg += ' must be of urlParser.url_object type.'
            raise ValueError( msg )

        self._uri = url_object( uri.url_string.replace(' ', '%20') )
        self._url = self._uri.uri2url()
        
    def setMethod( self , method ):
        self._method = method
        
    def setDc(self, dataCont):
        if not isinstance(dataCont, dataContainer):
            raise TypeError('Invalid call to fuzzableRequest.setDc(), the '
                            'argument must be a dataContainer instance.')
        self._dc = dataCont
        
    def setHeaders( self , headers ):
        self._headers = headers
    
    def setReferer( self, referer ):
        self._headers[ 'Referer' ] = referer
    
    def setCookie( self , c ):
        '''
        @parameter cookie: A cookie object as defined in core.data.dc.cookie,
            or a string.
        '''
        if isinstance( c, cookie):
            self._cookie = c
        elif isinstance( c, basestring ):
            self._cookie = cookie( c )
        elif c is None:
            self._cookie = None
        else:
            om.out.error('[fuzzableRequest error] setCookie received: "' + str(type(c)) + '" , "' + repr(c) + '"'  )
            raise w3afException('Invalid call to fuzzableRequest.setCookie()')
            
    def getURL( self ):
        return self._url
    
    def getURI( self ):
        return self._uri
        
    def setData( self, d ):
        '''
        The data is the string representation of the dataContainer, in most 
        cases it wont be set.
        '''
        self._data = d
        
    def getData( self ):
        '''
        The data is the string representation of the dataContainer, in most
        cases it will be used as the POSTDATA for requests. Sometimes it is
        also used as the query string data.
        '''
        return self._data
        
    def getMethod( self ):
        return self._method
        
    def getDc( self ):
        return self._dc
        
    def getHeaders( self ):
        return self._headers
    
    def getReferer( self ):
        if 'Referer' in self._headers['headers']:
            return self._headers['Referer']
        else:
            return ''
    
    def getCookie( self ):
        if self._cookie:
            return self._cookie
        else:
            return None
    
    def getFileVariables( self ):
        return []
    
    def copy( self ):
        return copy.deepcopy(self)
