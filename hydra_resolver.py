#! /usr/bin/python
#--- Hydra Resolver
#--- An asynchronous hostname resolver powered by Twisted
#--- Give it a list of hostnames and it will return a dictionary of answers
#--- @author: Nick Summerlin
#--- @last_modified: 2013-06-02

import twisted.names as tn

from sys import exit
from random import choice
from socket import inet_ntop, AF_INET6
from collections import defaultdict

from twisted.internet import reactor, defer
from twisted.names.client import Resolver
from twisted.python import log

class CustomResolver(Resolver):
    def __init__(self, flag=False, servers=[('8.8.8.8', 53)], timeout=(2, 3, 5, 10)):
        Resolver.__init__(self, servers=servers, timeout=timeout)
        self.flag = flag
        self.servers = servers

        # load TLD nameservers
        if self.flag:
            from pickle import load
            self.tld_servers = load(open('/usr/local/share/tld_nameservers.pkl'))

    def queryUDP(self, queries, timeout = None):
        """ Make a number of DNS queries via UDP.
            @type queries: A C{list} of C{dns.Query} instances
            @param queries: The queries to make.

            @type timeout: Sequence of C{int}
            @param timeout: Number of seconds after which to reissue the query.
            When the last timeout expires, the query is considered failed.

            @rtype: C{Deferred}
            @raise C{twisted.internet.defer.TimeoutError}: When the query times out.
        """
        if timeout is None:
            timeout = self.timeout

        addresses = list(self.servers)

        if self.flag:
            query = queries[0]
            hostname = query.name.name
            tld = hostname.split('.')[-1]
            try:
                addresses = self.tld_servers[tld.lower()]
            except KeyError as e:
                log.err("TLD {} not found in tld_servers.pkl".format(tld))
  
        # choose a random server from the list 
        used = choice(addresses)
        addresses.remove(used)

        d = self._query(used, queries, timeout[0])
        d.addErrback(self._reissue, addresses, [used], queries, timeout)
        return d

class HydraResolver(object):
    def __init__(self, flag=False, servers=[('8.8.8.8', 53)], timeout=(1, 3, 5, 7)):
        
        # custom resolver class that can issue queries directly to the TLD nameserver
        self.resolver = CustomResolver(flag=flag, servers=servers, timeout=timeout)
    
        # rfc 2136 gives us a mapping for opcode value -> mneumonic 
        self.rcode = defaultdict(lambda: 'UNRECOGNIZED_RCODE')
        self.rcode.update({ 0: 'OK', 1: 'FORMERR', 2: 'SERVFAIL', 
                            3: 'NXDOMAIN', 4: 'NOTIMP', 5: 'REFUSED' })
        
        # a mapping of query type -> Resolver.function
        self.query_type = defaultdict(lambda: 'lookupAddress')
        self.query_type.update({ 'A': 'lookupAddress', 
                                'ANY': 'lookupAllRecords', 
                                'NS': 'lookupNameservers', 
                                'TEXT': 'lookupText', 
                                'SOA': 'lookupAuthority', 
                                'AAAA': 'lookupIPV6Address' })
        
        self.results = {}
    
    @defer.inlineCallbacks
    def _do_lookup(self, hostname, type='A'):
        ''' Perform a DNS lookup on a hostname and defer the result
            @param: hostname, the hostname to lookup (str)
            @param: type, the type of query to make (A, NS, ANY, MX, etc)
            @return: a two-tuple with the hostname and response
            @TODO: the lookup functions are supposed to be able to take a timeout 
                   as a parameter. didn't seem to work when i tried it.
            @author: Nick Summerlin
        '''
        response = yield getattr(self.resolver, self.query_type[type])(hostname)
        defer.returnValue((hostname, response))
    
    def _got_result(self, result):
        ''' Callback that takes the response from _do_lookup and transforms each answer
            into a dictionary and places them into a list. The list is then entered 
            into a class level dictionary. 
            @param: result, a two-tuple of hostname (str) and RRHeaders ([Answer], [Auth], [Add'l])
            @TODO: NAPTR records aren't handled cleanly (no exceptions thrown, but instead
                   of legible ASCII, you get a Record_NAPTR object)
        '''
        hostname = result[0]
     
        answer_section = result[1][0]
        authority_section = result[1][1]
        additional_section = result[1][2]
    
        self.results[hostname]['status'] = 'NOERROR'
        
        if len(answer_section) > 0:
            self.results[hostname]['answer'] = []
            # for answer in RRHeader
            for rr in answer_section:
                self.results[hostname]['answer'].append(self._jsonify(rr))
    
        if len(authority_section) > 0:
            self.results[hostname]['authority'] = []
            # for answer in RRHeader
            for rr in authority_section:
                self.results[hostname]['authority'].append(self._jsonify(rr))
    
        if len(additional_section) > 0:
            self.results[hostname]['additional'] = []
            # for answer in RRHeader
            for rr in additional_section:
                self.results[hostname]['additional'].append(self._jsonify(rr))
    
        if len(answer_section) == 0 and len(authority_section) == 0 and len(additional_section) == 0:
            self.results[hostname]['status'] = 'NO_ANSWER'
    
    def _got_failure(self, failure):
        ''' Errback for _do_lookup, rcodes like NXDOMAIN and SERVFAIL
            will throw a DomainError, which contains the resulting dns.Message.
            We can retrieve the rcode from the dns.Message to determine the status.
            @param: failure, twisted.failure (wrapper for an Exception)
        '''
        # if we got a twisted.names.error.DomainError
        if (isinstance(failure.value, tn.error.DomainError) and 
            isinstance(failure.value.message, tn.dns.Message)):
            # pull out the message
            msg = failure.value.message
            # pull out hostname from Message
            hostname = msg.queries[0].name.name
            # map the response code to a meaningful message 
            self.results[hostname]['status'] = self.rcode[msg.rCode]
        elif (isinstance(failure.value, tn.error.DNSQueryTimeoutError)):
            #import pickle
            #with open('/tmp/timeout_error', 'w') as f:
            #    pickle.dump(failure, f)
            #print failure.printTraceback()
            pass
        else:
            # got some other error type of error
            #import pickle
            #with open('/tmp/_got_failure', 'w') as f:
            #    pickle.dump(failure, f)
            #print failure.printTraceback()
            #exit()
            pass    
    
    def resolve_list(self, hostname_list, qtype='A', tokens=300):
        ''' Resolves a list of hostnames asynchronously using Twisted
            @param: hostname_list, list of hostnames (str)
            @param: nameservers, a list of nameservers you wish to query
            @return: a dictionary where the keys are hostnames and the values
                     are lists of IP addresses (dotted quad format)
        '''
        jobs = []
        # a semaphore to limit the number of concurrent jobs
        # if token=100 then job 101 will wait until a previous job completes
        sem = defer.DeferredSemaphore(tokens)
        # create a deferred for each hostname
        for host in hostname_list:
            self.results[host] = {}
            self.results[host]['status'] = 'TIMEOUT'
            d = sem.run(self._do_lookup, host, qtype.upper())
            d.addCallbacks(self._got_result, self._got_failure)
            jobs.append(d)

        # gather the results 
        d = defer.gatherResults(jobs, consumeErrors=False)
        # stop the reactor when we're done
        d.addCallback(lambda fin: reactor.stop())
    
        reactor.run()
    
        return self.results
    
    def _jsonify(self, record):
        ''' Takes an RRHeader and creates a dict with it's attributes
            @param: record, an RRHeader object
            @return: data, a dict representing the RRHeader's data
        '''
        data = {}
        data['name'] = record.name.name
    
        # if rr contains A record
        if isinstance(record.payload, tn.dns.Record_A):
            self._jsonify_A(record.payload, data)
        # if record contains AAAA record
        elif isinstance(record.payload, tn.dns.Record_AAAA):
            self._jsonify_AAAA(record.payload, data)
        # else record contains different type of record
        else:
            self._jsonify_default(record.payload, data)
    
        return data
    
    def _jsonify_default(self, payload, data):
        data['type'] = payload.fancybasename
    
        for k,v in payload.__dict__.items():
            if isinstance(v, tn.dns.Name):
                data[k] = v.name
            else:
                data[k] = v
    
    def _jsonify_A(self, payload, data):
        ''' Takes a 'Record_A' object and adds it's data to the passed 'data' dict
            @param: payload, twisted.names.dns.Record_A object
            @param: data, dict containing RRHeader data
        '''
        data['type'] = 'A'
        data['ttl'] = payload.ttl
        data['address'] = payload.dottedQuad()
    
    def _jsonify_AAAA(self, payload, data):
        ''' Takes a 'Record_AAAA' object and adds it's data to the passed 'data' dict
            @param: payload, twisted.names.dns.Record_A object
            @param: data, dict containing RRHeader data
        '''
        data['type'] = 'AAAA'
        data['ttl'] = payload.ttl
        data['address'] = inet_ntop(AF_INET6, payload.address)

if __name__ == "__main__":
    ''' Example usage '''
    from pprint import pprint 
    hostnames = ['twistedmatrix.com', 'google.com', 'apple.com', 'yahoo.com', 'facebook.com', 'youtube.com', 'thedomainthatdoesntexist.com', 'megaupload.com', 'media.tumblr.com', 'abcnews.go.com']
    
    hydra = HydraResolver()
    result = hydra.resolve_list(hostnames)
    
    pprint(result)
