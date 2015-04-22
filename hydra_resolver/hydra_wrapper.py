#! /usr/bin/python
#--- Wrapper for Hydra Resolver
#--- An asynchronous hostname resolver powered by Twisted.
#--- The Twisted reactor cannot be stopped and restarted, so  
#--- the wrapper runs each batch resolver job in a separate process. 
#--- @author: Nick Summerlin
#--- @last_modified: 2015-04-22

from hydra_resolver import HydraResolver

from multiprocessing import Process, Pipe

def _resolve_list(pipe, hostname_list, qtype='A', tokens=300, flag=False, servers=[('8.8.8.8', 53)], timeout=(1, 3, 5, 7)):
    hydra = HydraResolver(flag=flag, servers=servers, timeout=timeout)
    result = hydra.resolve_list(hostname_list, qtype=qtype, tokens=tokens)
    pipe.send(result)
    pipe.close()

def resolve_list(hostname_list, qtype='A', tokens=300, flag=False, servers=[('8.8.8.8', 53)], timeout=(1, 3, 5, 7)):
    parent, child = Pipe()
    p = Process(target=_resolve_list, args=(child, hostname_list, qtype, tokens, flag, servers, timeout))
    p.start()
    result = parent.recv()
    p.join()
    return result