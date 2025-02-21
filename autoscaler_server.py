import grpc
from concurrent import futures
import time
import autoscaler_pb2
import autoscaler_pb2_grpc
from kubernetes import config, client

config.load_kube_config()

class AutoScalerService(autoscaler_pb2_grpc.AutoScalerServicer):

    def GetMetrics(self, request, context):
        v1 = client.CustomObjectsApi()
        try:
            metrics = v1.list_namespaced_custom_object(
                group="metrics.k8s.io",
                version='v1beta1',
                namespace=request.namespace,
                plural="pods"
            )

            total_cpu = 0.0
            total_memory = 0.0
            pod_count = len(metrics["items"])

            for pod in metrics["items"]:
                for container in pod["containers"]:
                    cpu_usage = container["usage"]["cpu"]
                    memory_usage = container["usage"]["memory"]

                    total_cpu += self.convert_cpu(cpu_usage)
                    total_memory += self.convert_memory(memory_usage) 


            avg_cpu = total_cpu / pod_count if pod_count else 0
            avg_memory = total_memory / pod_count if pod_count else 0

            return autoscaler_pb2.MetricsResponse(namespace=request.namespace, cpu_usage=avg_cpu, memory_usage=avg_memory)
        
        except KeyError as e:
            print(f"KeyError: {e} - Check if 'namespace' exists in metrics")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details("Failed to fetch metrics due to missing data")
            return autoscaler_pb2.MetricsResponse(cpu_usage=0.0, memory_usage=0.0)
        except Exception as e:
            print(f"Error fetching metrics: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details("Failed to fetch metrics")
            return autoscaler_pb2.MetricsResponse(cpu_usage=0.0, memory_usage=0.0)
        
    
    def ScalePods(self, request, context):

        v1 = client.AppsV1Api()

        try:
            # update deployments replica count
            body = {"spec": {"replicas": request.replicas}}
            v1.patch_namespaced_deployment_scale(
                name="autoscaler-deployment",
                namespace=request.namespace,
                body=body,
            )

            return autoscaler_pb2.ScaleResponse(message=f"Scaled to {request.replicas} replicas.")
        
        except Exception as e:
            print("error scaling pods! see: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details("Failed to scale pods")
            return autoscaler_pb2.ScaleResponse(message="Scaling failed.")
        
    
    # converts cpu units to float
    def convert_cpu(self, cpu_value):
        if cpu_value.endswith("m"):
            return float(cpu_value[:-1]) / 1000
        return float(cpu_value)
    
    def convert_memory(self, memory_value):
        if memory_value.endswith("Ki"):
            return float(memory_value[:-2]) / 1024
        if memory_value.endswith("Mi"):
            return float(memory_value[:-2])
        if memory_value.endswith("Gi"):
            return float(memory_value[:-2]) * 1024
        return float(memory_value)
    

def serve():
    # start server

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    autoscaler_pb2_grpc.add_AutoScalerServicer_to_server(AutoScalerService(), server)
    server.add_insecure_port("[::]:50051")
    print("🚀 gRPC AutoScaler Server started on port 50051")
    
    server.start()
    try:
        while True:
            time.sleep(86400)  # Keep running
    except KeyboardInterrupt:
        server.stop(0)

if __name__ == "__main__":
    serve()