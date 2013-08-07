#Notice
cp tld_nameservers.pkl into /usr/local/share/

# hydra_resolver


### An asynchronous hostname resolver powered by Twisted

I needed a utility to resolve a lot of hostnames and I wanted to learn asynchronous programming with [Twisted](http://twistedmatrix.com), this is the result.

If you want pure speed, [adns](https://code.google.com/p/adns-python/) is faster. It's based on the [adns resolver library](http://www.chiark.greenend.org.uk/~ian/adns/) (written in C).

Hydra isn't far behind [adns](https://code.google.com/p/adns-python/) in terms of speed and it's extremely easy to use. 

###Examples

By default, hydra will attempt to retrieve all A records from a list of hostnames. 

```
from hydra_resolver import HydraResolver
from pprint import pprint 

hostnames = ['twistedmatrix.com', 'google.com', 'facebook.com', 'thedomainthatdoesntexist.com']

hydra = HydraResolver()
result = hydra.resolve_list(hostnames)

pprint(result)
```


Gives you:

```
{'facebook.com': [{'address': '173.252.110.27', 'ttl': 875, 'type': 'A'}],
 'google.com': [{'address': '173.194.33.2', 'ttl': 295, 'type': 'A'},
                {'address': '173.194.33.0', 'ttl': 295, 'type': 'A'},
                {'address': '173.194.33.4', 'ttl': 295, 'type': 'A'},
                {'address': '173.194.33.7', 'ttl': 295, 'type': 'A'},
                {'address': '173.194.33.8', 'ttl': 295, 'type': 'A'},
                {'address': '173.194.33.5', 'ttl': 295, 'type': 'A'},
                {'address': '173.194.33.6', 'ttl': 295, 'type': 'A'},
                {'address': '173.194.33.14', 'ttl': 295, 'type': 'A'},
                {'address': '173.194.33.3', 'ttl': 295, 'type': 'A'},
                {'address': '173.194.33.1', 'ttl': 295, 'type': 'A'},
                {'address': '173.194.33.9', 'ttl': 295, 'type': 'A'}],
 'thedomainthatdoesntexist.com': 'NXDOMAIN',
 'twistedmatrix.com': [{'address': '66.35.39.65', 'ttl': 12519, 'type': 'A'}]
 }
```

If you want to get other types of records, simply pass the query type into `resolve_list` like this: 

```
from hydra_resolver import HydraResolver
from pprint import pprint 

hostnames = ['twistedmatrix.com', 'google.com', 'facebook.com', 'thedomainthatdoesntexist.com']

hydra = HydraResolver()

# you can pass most valid query types to resolve_list
result = hydra.resolve_list(hostnames, 'SOA')
pprint(result)
```


Gives you:

```
{'facebook.com': [{'expire': 604800,
                   'minimum': 120,
                   'mname': 'a.ns.facebook.com',
                   'refresh': 7200,
                   'retry': 1800,
                   'rname': 'dns.facebook.com',
                   'serial': 2013040302,
                   'ttl': 116,
                   'type': 'SOA'}],
 'google.com': [{'expire': 1209600,
                 'minimum': 300,
                 'mname': 'ns1.google.com',
                 'refresh': 7200,
                 'retry': 1800,
                 'rname': 'dns-admin.google.com',
                 'serial': 2013031900,
                 'ttl': 21595,
                 'type': 'SOA'}],
 'thedomainthatdoesntexist.com': 'NXDOMAIN',
 'twistedmatrix.com': [{'expire': 86400,
                        'minimum': 86400,
                        'mname': 'ns1.twistedmatrix.com',
                        'refresh': 86400,
                        'retry': 900,
                        'rname': 'radix.twistedmatrix.com',
                        'serial': 2013040400,
                        'ttl': 21596,
                        'type': 'SOA'},
                       {'expire': 86400,
                        'minimum': 86400,
                        'mname': 'ns1.twistedmatrix.com',
                        'refresh': 86400,
                        'retry': 900,
                        'rname': 'radix.twistedmatrix.com',
                        'serial': 2013040400,
                        'ttl': 21596,
                        'type': 'SOA'}]
}
```

### Dependencies

[Twisted](http://twistedmatrix.com/trac/wiki/Downloads) is installed by default on many operating systems, but I'd recommend fetching and building the latest stable versions of [Twisted](http://twistedmatrix.com/Releases/Twisted/13.0/Twisted-13.0.0.tar.bz2), [Twisted-Core](http://twistedmatrix.com/Releases/Core/13.0/TwistedCore-13.0.0.tar.bz2), and [Twisted-Names](http://twistedmatrix.com/Releases/Names/13.0/TwistedNames-13.0.0.tar.bz2). Twisted was at version 13 when I wrote this doc. [Click here for information on how to get Twisted installed on your OS](http://twistedmatrix.com/trac/wiki/Downloads).
