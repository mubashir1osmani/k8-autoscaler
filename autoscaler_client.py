import grpc
import autoscaler_pb2_grpc
import autoscaler_pb2

def get_metrics(stub, namespace):
    # fetch and display cpu metrics for a namespace
    request = autoscaler_pb2.MetricsRequest(namespace=namespace)
    response = stub.GetMetrics(request)
    print(f"Namespace: {namespace}")
    print(f"CPU USAGE: {response.cpu_usage:2.f} cores")
    print(f"MEMORY USAGE! {response.memory_usage: 2.f} mb\n")

def scale_pods(stub, namespace, replicas):
    # here we wanna show how many replicas we create

    request = autoscaler_pb2.ScalePods(namespace=namespace, replicas=replicas)
    response = stub.ScalePods(request)

    print(f"scaled to: {response.message}")

def run():
    # run it!

    channel = grpc.insecure_channel("localhost:50051")
    stub = autoscaler_pb2_grpc.AutoScalerStub(channel)
    namespace="default"

    # fetch metrics and scale pods
    get_metrics(stub, namespace)
    replicas = int(input("enter new replica count: "))
    scale_pods(stub, namespace, replicas)


if __name__ == "__main__":
    run()
