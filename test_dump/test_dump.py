import os
import json
import time
import resource

def test_dump(client, db):
    # find all query_path file in nexus_use_case_dump directory
    query_path_files = []
    for root, dirs, files in os.walk('../nexus_use_case_dump'):
        for file in files:
            if file.endswith('query_path'):
                query_path_files.append(os.path.join(root, file))
    
    urls = []
    for file_path in query_path_files:
        with open(file_path, 'r') as file:
            url = file.read().strip()
            if "files" in url:
                continue
            if "resolver" in url:
                continue
            urls.append({"file":file_path, "url":url.replace("https://openbluebrain.com/api","")})
    total_elapsed_time = 0
    total_cpu_time = 0
    nb_calls = 0
    nb_failures = 0
    for url in urls:
        if "resources" in url["url"]:
            nb_calls += 1
            start_time = time.time()
            start_resources = resource.getrusage(resource.RUSAGE_SELF)

            ret = client.get(url["url"])
            

            end_time = time.time()
            end_resources = resource.getrusage(resource.RUSAGE_SELF)

            elapsed_time = end_time - start_time
            cpu_time = end_resources.ru_utime - start_resources.ru_utime
            total_elapsed_time += elapsed_time
            total_cpu_time += cpu_time
            if ret.status_code != 200:
                nb_failures += 1
        else:
            nb_calls += 1
            json_data = {}
            file_name =  url["file"].replace("query_path","query_body.json")
            with open(file_name, 'r') as file:
                json_data = json.load(file)

            start_time = time.time()
            start_resources = resource.getrusage(resource.RUSAGE_SELF)
            client.post(url["url"], data=json_data)

            end_time = time.time()
            end_resources = resource.getrusage(resource.RUSAGE_SELF)

            elapsed_time = end_time - start_time
            cpu_time = end_resources.ru_utime - start_resources.ru_utime
            total_elapsed_time += elapsed_time
            total_cpu_time += cpu_time
            if ret.status_code != 200:
                nb_failures += 1
    print(f"Elapsed time: {total_elapsed_time} seconds")
    print(f"CPU time: {total_cpu_time} seconds")
    print(f"Number of calls: {nb_calls}")
    print(f"Number of failures: {nb_failures}")