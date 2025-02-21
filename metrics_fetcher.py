from prometheus_api_client import PrometheusConnect
prom = PrometheusConnect(url="http://localhost:9090", disable_ssl=True)

def get_cpu_usage():
    query = 'sum(container_cpu_usage_set_bytes)'
    result = prom.custom_query(query=query)
    return result

def get_memory_usage():
    query = 'sum(container_memory_set_bytes)'
    result = prom.custom_query(query=query)
    return result

if __name__ == "__main__":
    print("cPU usage:", get_cpu_usage())
    print("memory usage:", get_memory_usage()) 
