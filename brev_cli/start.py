from watchgod import awatch
import asyncio
import json
from functools import wraps
import time
import sys
import threading
import getpass

user = getpass.getuser()

sys.path.insert(1, "/Users/" + user + "/Desktop/brev/brev_cli/brev_cli")


import helpers







def coro(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))

    return wrapper


@coro
async def start():


    # curr_dir = os.getcwd()

    # endpoints = helpers.get_endpoints(write=False, init=False, custom_dir=curr_dir)

    # endpoint_paths = []


    # for endpoint in endpoints:
    #     endpoint_paths.append(curr_dir + "/" + endpoint["name"] + ".py")
    #     os.environ[endpoint["name"]] = ""
    # print(endpoint_paths)
    print("asdasasdd")
    
    active_file = open("/Users/josephyeh/.brev/active_projects.json")
    active_projects = json.load(active_file)





    async for changes in watch_multiple(active_projects):
        changed_file = changes.pop()[1]
        print(changed_file)
        endpoint_path = "/".join(changed_file.split("/")[:-1])
        endpoint = changed_file.split("/")[-1][:-3]
        helpers.update_endpoint(endpoint_path, endpoint)



    # print("asdasdasd")
    # while True:



    #     # stamp = os.stat(os.getcwd()+"/brev_cli/commands.py").st_mtime
    #     # data = fd.read()
    #     for i in range(len(endpoints)):
    #         stamp = os.stat(endpoint_paths[i]).st_mtime
    #         if str(stamp) != os.environ[endpoints[i]["name"]]:
    #             print(endpoints[i]["name"])
    #             os.environ[endpoints[i]["name"]] = str(stamp)
    #             helpers.update(endpoints[i]["name"])
    #     time.sleep(1)



async def watch_multiple(paths):
    watchers = [awatch(p) for p in paths]
    while True:
        done, pending = await asyncio.wait([w.__anext__() for w in watchers], return_when=asyncio.FIRST_COMPLETED)
        for t in pending:
            t.cancel()
        for t in done:
            yield t.result()



def main():
    print(1)

def test():
    print(2)
    

    
if __name__ == "__main__":
    
    if len(sys.argv[1:]) == 0:
        print("start")
    else:
        start()
    
