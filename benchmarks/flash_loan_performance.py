#!/usr/bin/env python3
"""
Flash Loan Performance Benchmarks
Performance testing and benchmarking for flash loan operations
"""

import asyncio
import aiohttp
import time
import statistics
import json
from typing import Dict, List, Any
from dataclasses import dataclass

@dataclass
class BenchmarkResult:
    operation: str
    avg_latency: float
    min_latency: float
    max_latency: float
    p95_latency: float
    success_rate: float
    throughput: float
    total_requests: int

class FlashLoanBenchmark:
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def benchmark_price_feed_latency(self, num_requests: int = 100) -> BenchmarkResult:
        """Benchmark price feed response latency."""
        url = f"{self.base_url}/price-feed/prices"
        
        latencies = []
        successful_requests = 0
        
        start_time = time.time()
        
        for _ in range(num_requests):
            request_start = time.time()
            try:
                async with self.session.get(url, timeout=10) as response:
                    await response.read()
                    request_end = time.time()
                    
                    if response.status == 200:
                        successful_requests += 1
                        latencies.append(request_end - request_start)
            except Exception:
                pass
        
        end_time = time.time()
        total_duration = end_time - start_time
        
        if not latencies:
            return BenchmarkResult(
                operation="price_feed",
                avg_latency=0,
                min_latency=0,
                max_latency=0,
                p95_latency=0,
                success_rate=0,
                throughput=0,
                total_requests=num_requests
            )
        
        return BenchmarkResult(
            operation="price_feed",
            avg_latency=statistics.mean(latencies),
            min_latency=min(latencies),
            max_latency=max(latencies),
            p95_latency=statistics.quantiles(latencies, n=20)[18] if len(latencies) > 1 else latencies[0],
            success_rate=successful_requests / num_requests,
            throughput=successful_requests / total_duration,
            total_requests=num_requests
        )
    
    async def benchmark_arbitrage_detection(self, num_requests: int = 50) -> BenchmarkResult:
        """Benchmark arbitrage opportunity detection speed."""
        url = f"{self.base_url}/arbitrage/opportunities"
        
        latencies = []
        successful_requests = 0
        
        start_time = time.time()
        
        for _ in range(num_requests):
            request_start = time.time()
            try:
                async with self.session.get(url, timeout=15) as response:
                    await response.read()
                    request_end = time.time()
                    
                    if response.status == 200:
                        successful_requests += 1
                        latencies.append(request_end - request_start)
            except Exception:
                pass
        
        end_time = time.time()
        total_duration = end_time - start_time
        
        if not latencies:
            return BenchmarkResult(
                operation="arbitrage_detection",
                avg_latency=0,
                min_latency=0,
                max_latency=0,
                p95_latency=0,
                success_rate=0,
                throughput=0,
                total_requests=num_requests
            )
        
        return BenchmarkResult(
            operation="arbitrage_detection",
            avg_latency=statistics.mean(latencies),
            min_latency=min(latencies),
            max_latency=max(latencies),
            p95_latency=statistics.quantiles(latencies, n=20)[18] if len(latencies) > 1 else latencies[0],
            success_rate=successful_requests / num_requests,
            throughput=successful_requests / total_duration,
            total_requests=num_requests
        )
    
    async def benchmark_flash_loan_simulation(self, num_requests: int = 20) -> BenchmarkResult:
        """Benchmark flash loan simulation performance."""
        url = f"{self.base_url}/flash-loan/simulate"
        
        payload = {
            "token_address": "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619",
            "amount": "1000000000000000000",
            "strategy": "simple_arbitrage",
            "dex_route": ["uniswap", "sushiswap"]
        }
        
        latencies = []
        successful_requests = 0
        
        start_time = time.time()
        
        for _ in range(num_requests):
            request_start = time.time()
            try:
                async with self.session.post(url, json=payload, timeout=20) as response:
                    await response.read()
                    request_end = time.time()
                    
                    if response.status == 200:
                        successful_requests += 1
                        latencies.append(request_end - request_start)
            except Exception:
                pass
        
        end_time = time.time()
        total_duration = end_time - start_time
        
        if not latencies:
            return BenchmarkResult(
                operation="flash_loan_simulation",
                avg_latency=0,
                min_latency=0,
                max_latency=0,
                p95_latency=0,
                success_rate=0,
                throughput=0,
                total_requests=num_requests
            )
        
        return BenchmarkResult(
            operation="flash_loan_simulation",
            avg_latency=statistics.mean(latencies),
            min_latency=min(latencies),
            max_latency=max(latencies),
            p95_latency=statistics.quantiles(latencies, n=20)[18] if len(latencies) > 1 else latencies[0],
            success_rate=successful_requests / num_requests,
            throughput=successful_requests / total_duration,
            total_requests=num_requests
        )
    
    async def benchmark_concurrent_operations(self, concurrent_users: int = 10, requests_per_user: int = 5) -> BenchmarkResult:
        """Benchmark system under concurrent load."""
        urls = [
            f"{self.base_url}/price-feed/prices",
            f"{self.base_url}/arbitrage/opportunities",
            f"{self.base_url}/blockchain/mempool"
        ]
        
        async def user_session(user_id: int) -> List[float]:
            """Simulate a user making multiple requests."""
            user_latencies = []
            
            for _ in range(requests_per_user):
                for url in urls:
                    request_start = time.time()
                    try:
                        async with self.session.get(url, timeout=10) as response:
                            await response.read()
                            request_end = time.time()
                            
                            if response.status == 200:
                                user_latencies.append(request_end - request_start)
                    except Exception:
                        pass
                    
                    # Small delay between requests
                    await asyncio.sleep(0.1)
            
            return user_latencies
        
        start_time = time.time()
        
        # Create concurrent user sessions
        user_tasks = [user_session(i) for i in range(concurrent_users)]
        user_results = await asyncio.gather(*user_tasks)
        
        end_time = time.time()
        total_duration = end_time - start_time
        
        # Flatten all latencies
        all_latencies = []
        for user_latencies in user_results:
            all_latencies.extend(user_latencies)
        
        total_requests = concurrent_users * requests_per_user * len(urls)
        successful_requests = len(all_latencies)
        
        if not all_latencies:
            return BenchmarkResult(
                operation="concurrent_operations",
                avg_latency=0,
                min_latency=0,
                max_latency=0,
                p95_latency=0,
                success_rate=0,
                throughput=0,
                total_requests=total_requests
            )
        
        return BenchmarkResult(
            operation="concurrent_operations",
            avg_latency=statistics.mean(all_latencies),
            min_latency=min(all_latencies),
            max_latency=max(all_latencies),
            p95_latency=statistics.quantiles(all_latencies, n=20)[18] if len(all_latencies) > 1 else all_latencies[0],
            success_rate=successful_requests / total_requests,
            throughput=successful_requests / total_duration,
            total_requests=total_requests
        )
    
    async def benchmark_risk_assessment_speed(self, num_requests: int = 30) -> BenchmarkResult:
        """Benchmark risk assessment calculation speed."""
        url = f"{self.base_url}/risk-manager/assess"
        
        payload = {
            "transaction_type": "flash_loan",
            "amount": "5000000000000000000",  # 5 ETH
            "token_address": "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619",
            "strategy": "triangular_arbitrage"
        }
        
        latencies = []
        successful_requests = 0
        
        start_time = time.time()
        
        for _ in range(num_requests):
            request_start = time.time()
            try:
                async with self.session.post(url, json=payload, timeout=15) as response:
                    await response.read()
                    request_end = time.time()
                    
                    if response.status == 200:
                        successful_requests += 1
                        latencies.append(request_end - request_start)
            except Exception:
                pass
        
        end_time = time.time()
        total_duration = end_time - start_time
        
        if not latencies:
            return BenchmarkResult(
                operation="risk_assessment",
                avg_latency=0,
                min_latency=0,
                max_latency=0,
                p95_latency=0,
                success_rate=0,
                throughput=0,
                total_requests=num_requests
            )
        
        return BenchmarkResult(
            operation="risk_assessment",
            avg_latency=statistics.mean(latencies),
            min_latency=min(latencies),
            max_latency=max(latencies),
            p95_latency=statistics.quantiles(latencies, n=20)[18] if len(latencies) > 1 else latencies[0],
            success_rate=successful_requests / num_requests,
            throughput=successful_requests / total_duration,
            total_requests=num_requests
        )
    
    def print_result(self, result: BenchmarkResult):
        """Print benchmark result in a formatted way."""
        print(f"\n{'='*60}")
        print(f"BENCHMARK RESULTS: {result.operation.upper()}")
        print(f"{'='*60}")
        print(f"Total Requests:    {result.total_requests}")
        print(f"Success Rate:      {result.success_rate:.2%}")
        print(f"Throughput:        {result.throughput:.2f} req/s")
        print(f"Average Latency:   {result.avg_latency*1000:.2f} ms")
        print(f"Min Latency:       {result.min_latency*1000:.2f} ms")
        print(f"Max Latency:       {result.max_latency*1000:.2f} ms")
        print(f"95th Percentile:   {result.p95_latency*1000:.2f} ms")
        
        # Performance assessment
        if result.avg_latency < 0.1:  # 100ms
            print(f"Performance:       ✅ EXCELLENT")
        elif result.avg_latency < 0.5:  # 500ms
            print(f"Performance:       ✅ GOOD")
        elif result.avg_latency < 1.0:  # 1s
            print(f"Performance:       ⚠️  ACCEPTABLE")
        else:
            print(f"Performance:       ❌ NEEDS IMPROVEMENT")
    
    def save_results_to_file(self, results: List[BenchmarkResult], filename: str = None):
        """Save benchmark results to JSON file."""
        if filename is None:
            filename = f"benchmark_results_{int(time.time())}.json"
        
        results_data = []
        for result in results:
            results_data.append({
                "operation": result.operation,
                "avg_latency_ms": result.avg_latency * 1000,
                "min_latency_ms": result.min_latency * 1000,
                "max_latency_ms": result.max_latency * 1000,
                "p95_latency_ms": result.p95_latency * 1000,
                "success_rate": result.success_rate,
                "throughput_rps": result.throughput,
                "total_requests": result.total_requests,
                "timestamp": time.time()
            })
        
        with open(filename, 'w') as f:
            json.dump(results_data, f, indent=2)
        
        print(f"\n📊 Results saved to: {filename}")

async def main():
    """Run all benchmarks."""
    print("🚀 Starting Flash Loan Performance Benchmarks...")
    
    async with FlashLoanBenchmark() as benchmark:
        results = []
        
        # Run individual benchmarks
        print("\n1. Benchmarking Price Feed Latency...")
        price_feed_result = await benchmark.benchmark_price_feed_latency(100)
        benchmark.print_result(price_feed_result)
        results.append(price_feed_result)
        
        print("\n2. Benchmarking Arbitrage Detection...")
        arbitrage_result = await benchmark.benchmark_arbitrage_detection(50)
        benchmark.print_result(arbitrage_result)
        results.append(arbitrage_result)
        
        print("\n3. Benchmarking Flash Loan Simulation...")
        simulation_result = await benchmark.benchmark_flash_loan_simulation(20)
        benchmark.print_result(simulation_result)
        results.append(simulation_result)
        
        print("\n4. Benchmarking Risk Assessment...")
        risk_result = await benchmark.benchmark_risk_assessment_speed(30)
        benchmark.print_result(risk_result)
        results.append(risk_result)
        
        print("\n5. Benchmarking Concurrent Operations...")
        concurrent_result = await benchmark.benchmark_concurrent_operations(10, 3)
        benchmark.print_result(concurrent_result)
        results.append(concurrent_result)
        
        # Save results
        benchmark.save_results_to_file(results)
        
        # Overall assessment
        avg_success_rate = statistics.mean([r.success_rate for r in results])
        avg_latency = statistics.mean([r.avg_latency for r in results])
        
        print(f"\n{'='*60}")
        print(f"OVERALL SYSTEM PERFORMANCE")
        print(f"{'='*60}")
        print(f"Average Success Rate:  {avg_success_rate:.2%}")
        print(f"Average Latency:       {avg_latency*1000:.2f} ms")
        
        if avg_success_rate >= 0.95 and avg_latency < 0.5:
            print(f"System Status:         ✅ PRODUCTION READY")
        elif avg_success_rate >= 0.90 and avg_latency < 1.0:
            print(f"System Status:         ⚠️  NEEDS OPTIMIZATION")
        else:
            print(f"System Status:         ❌ NOT PRODUCTION READY")

if __name__ == "__main__":
    asyncio.run(main())
