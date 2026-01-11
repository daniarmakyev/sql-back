import asyncio
import httpx
import time

# Configuration
BASE_URL = "http://localhost:8000"
NUM_REQUESTS = 100
CONCURRENCY = 10

async def fetch(client, url):
    """Asynchronous function to fetch a URL."""
    try:
        start_time = time.time()
        response = await client.get(url)
        response.raise_for_status()  # Raise an exception for bad status codes
        end_time = time.time()
        return end_time - start_time, response.status_code
    except httpx.RequestError as e:
        print(f"An error occurred: {e}")
        return None, None

async def run_performance_test():
    """Runs the performance test."""
    print("--- Starting Performance Test ---")
    print(f"URL: {BASE_URL}/health")
    print(f"Total Requests: {NUM_REQUESTS}")
    print(f"Concurrency Level: {CONCURRENCY}")
    print("---------------------------------")

    latencies = []
    successful_requests = 0
    failed_requests = 0
    
    async with httpx.AsyncClient() as client:
        tasks = []
        for i in range(NUM_REQUESTS):
            task = asyncio.create_task(fetch(client, f"{BASE_URL}/health"))
            tasks.append(task)
            if len(tasks) >= CONCURRENCY or i == NUM_REQUESTS - 1:
                results = await asyncio.gather(*tasks)
                for latency, status_code in results:
                    if latency is not None:
                        latencies.append(latency)
                        successful_requests += 1
                    else:
                        failed_requests += 1
                tasks = []

    print("\n--- Test Results ---")
    if latencies:
        print(f"Successful Requests: {successful_requests}")
        print(f"Failed Requests: {failed_requests}")
        print(f"Average Latency: {sum(latencies) / len(latencies):.4f} seconds")
        print(f"Min Latency: {min(latencies):.4f} seconds")
        print(f"Max Latency: {max(latencies):.4f} seconds")
        
        sorted_latencies = sorted(latencies)
        p95_index = int(len(sorted_latencies) * 0.95)
        p99_index = int(len(sorted_latencies) * 0.99)
        print(f"95th Percentile Latency: {sorted_latencies[p95_index]:.4f} seconds")
        print(f"99th Percentile Latency: {sorted_latencies[p99_index]:.4f} seconds")
    else:
        print("No successful requests were made.")
    print("--------------------")

if __name__ == "__main__":
    asyncio.run(run_performance_test())
