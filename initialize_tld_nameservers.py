#! /usr/bin/python
#--- Script to populate TLD nameserver dictionary for HydraResolver
#--- @author: Nick Summerlin
#--- @last_modified: 2015-04-23

import requests
import dns.resolver
import pickle

TLD_LIST_URL = 'http://data.iana.org/TLD/tlds-alpha-by-domain.txt'

TLD_PKL = 'hydra_resolver/data/tld_nameservers.pkl'

resolver = dns.resolver.Resolver()

def fetch_tld_list():
    print "fetching tld list from {}".format(TLD_LIST_URL)
    resp = requests.get(TLD_LIST_URL)
    if resp.ok:
        tld_list = resp.content.split('\n')
        tld_list.pop(0)
        return tld_list
    else:
        raise Exception("Unable to fetch TLD list from {}".format(TLD_LIST_URL))

def get_tld_nameservers(tld):
    print "querying {} nameservers".format(tld)
    servers = set()
    try:
        ans = resolver.query(tld, 'NS')
        for rr in ans.rrset.items:
            a = resolver.query(rr.to_text())
            for record in a.rrset:
                servers.add(record.to_text())
    except Exception as e:
        print e.__class__, e.message
    return list(servers)

def main():
    tld_nameservers = {}
    fails = set()
    tld_list = fetch_tld_list()
    for tld in tld_list:
        nameservers = get_tld_nameservers(tld)
        if len(nameservers):
            ns_tuples = []
            for ip in nameservers:
                ns_tuples.append((ip, 53))
            tld_nameservers[tld.lower()] = ns_tuples
        else:
            fails.add(tld)

    with open(TLD_PKL, 'w') as f:
        pickle.dump(tld_nameservers, f)

    print "Received {} total TLDs from ICANN".format(len(tld_list))
    print "Successfully processed {} TLDs".format(len(tld_nameservers))
    print "The following TLDs failed for some reason"
    print fails

if __name__ == '__main__':
    main()