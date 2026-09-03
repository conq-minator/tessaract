"""
Asynchronous Worker Pool with Bounded Priority Queues.
Demonstrates async/await concurrency, producer-consumer queues, and graceful shutdown.
"""

import asyncio
import random
from typing import List, Dict, Any


class AsyncJobPool:
    def __init__(self, num_workers: int = 3, queue_capacity: int = 20):
        self.num_workers = num_workers
        self.queue: asyncio.Queue = asyncio.Queue(maxsize=queue_capacity)
        self.results: List[Dict[str, Any]] = []
        self.workers: List[asyncio.Task] = []
        self._total_processed: int = 0

    async def worker(self, worker_id: int):
        """Worker routine that continuously pulls and processes jobs from the queue."""
        while True:
            try:
                job_id, payload = await self.queue.get()
                # Simulate non-blocking asynchronous processing
                latency = random.uniform(0.01, 0.04)
                await asyncio.sleep(latency)
                
                res = {
                    "job_id": job_id,
                    "worker_id": worker_id,
                    "processed_payload": payload.upper(),
                    "latency_ms": round(latency * 1000, 2)
                }
                self.results.append(res)
                self._total_processed += 1
                self.queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Worker {worker_id} error: {e}")
                self.queue.task_done()

    async def run(self, jobs: List[Dict[str, Any]]):
        """Spawns workers, enqueues all jobs, and waits for completion."""
        # Start worker tasks
        for w_id in range(self.num_workers):
            task = asyncio.create_task(self.worker(w_id))
            self.workers.append(task)

        # Producer: Enqueue jobs
        for job in jobs:
            await self.queue.put((job["id"], job["data"]))

        # Wait until all items in the queue are processed
        await self.queue.join()

        # Graceful worker cancellation
        for task in self.workers:
            task.cancel()
        await asyncio.gather(*self.workers, return_exceptions=True)


async def main():
    print("[Async Worker Pool Demo] Launching Concurrent Task Orchestration...")
    pool = AsyncJobPool(num_workers=4)
    test_jobs = [{"id": i, "data": f"telemetry_packet_{i}"} for i in range(12)]
    
    await pool.run(test_jobs)
    
    print(f"Successfully processed {len(pool.results)} concurrent jobs across 4 workers.")
    for res in pool.results[:3]:
        print(f" -> Job #{res['job_id']} done by Worker {res['worker_id']} in {res['latency_ms']}ms")
    assert len(pool.results) == 12, "Job count mismatch!"
    print("[Async Worker Pool Demo] Status: SUCCESS - Async producer-consumer queue completed.")


if __name__ == "__main__":
    asyncio.run(main())
