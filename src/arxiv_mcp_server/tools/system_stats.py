"""System resource monitoring tool for informed converter selection."""

import json
import psutil
import platform
from typing import List, Dict, Any, Optional
import mcp.types as types
import logging
import asyncio

logger = logging.getLogger("arxiv-mcp-server.system-stats")


system_stats_tool = types.Tool(
    name="get_system_stats",
    description="Get current system resource usage (CPU, memory, GPU) to help decide which converter to use",
    inputSchema={
        "type": "object",
        "properties": {},
        "required": [],
    },
)


def get_gpu_info() -> Dict[str, Any]:
    """Get GPU information if available."""
    gpu_info = {"available": False}
    
    try:
        # Try to import and use GPUtil for NVIDIA GPUs
        import GPUtil
        gpus = GPUtil.getGPUs()
        if gpus:
            gpu = gpus[0]  # Get first GPU
            gpu_info = {
                "available": True,
                "name": gpu.name,
                "memory_total_mb": gpu.memoryTotal,
                "memory_used_mb": gpu.memoryUsed,
                "memory_free_mb": gpu.memoryFree,
                "utilization_percent": gpu.load * 100,
                "temperature_c": gpu.temperature
            }
    except ImportError:
        pass
    except Exception as e:
        logger.debug(f"GPU detection error: {e}")
    
    return gpu_info


def get_converter_recommendations(cpu_percent: float, memory_available_gb: float) -> Dict[str, str]:
    """Get converter recommendations based on system resources."""
    recommendations = {
        "recommended_converter": "pymupdf4llm",
        "can_use_marker": False,
        "reasoning": ""
    }
    
    # Check if system can handle marker-pdf
    if memory_available_gb < 4.0:
        recommendations["reasoning"] = f"Low memory ({memory_available_gb:.1f}GB available). marker-pdf needs 4GB+. Use pymupdf4llm."
        recommendations["can_use_marker"] = False
    elif cpu_percent > 80:
        recommendations["reasoning"] = f"High CPU usage ({cpu_percent:.0f}%). marker-pdf would overload system. Use pymupdf4llm."
        recommendations["can_use_marker"] = False
    elif memory_available_gb >= 8.0 and cpu_percent < 50:
        recommendations["reasoning"] = f"Good resources available ({memory_available_gb:.1f}GB RAM, {cpu_percent:.0f}% CPU). Can use marker-pdf if needed."
        recommendations["can_use_marker"] = True
    else:
        recommendations["reasoning"] = f"Moderate resources ({memory_available_gb:.1f}GB RAM, {cpu_percent:.0f}% CPU). pymupdf4llm recommended, marker-pdf possible but may be slow."
        recommendations["can_use_marker"] = True
    
    return recommendations


async def handle_system_stats(arguments: Dict[str, Any]) -> List[types.TextContent]:
    """Handle system stats request."""
    try:
        # Get CPU info
        cpu_count = psutil.cpu_count()
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_freq = psutil.cpu_freq()
        
        # Get memory info
        memory = psutil.virtual_memory()
        memory_total_gb = memory.total / (1024**3)
        memory_available_gb = memory.available / (1024**3)
        memory_used_gb = memory.used / (1024**3)
        memory_percent = memory.percent
        
        # Get disk info for storage path
        disk = psutil.disk_usage('/')
        disk_free_gb = disk.free / (1024**3)
        
        # Get system info
        system_info = {
            "platform": platform.system(),
            "platform_release": platform.release(),
            "architecture": platform.machine(),
            "python_version": platform.python_version()
        }
        
        # Get GPU info
        gpu_info = get_gpu_info()
        
        # Get process info
        current_process = psutil.Process()
        process_memory_mb = current_process.memory_info().rss / (1024**2)
        
        # Get converter recommendations
        recommendations = get_converter_recommendations(cpu_percent, memory_available_gb)
        
        # Compile results
        results = {
            "system": system_info,
            "cpu": {
                "count": cpu_count,
                "usage_percent": cpu_percent,
                "frequency_mhz": cpu_freq.current if cpu_freq else None
            },
            "memory": {
                "total_gb": round(memory_total_gb, 2),
                "available_gb": round(memory_available_gb, 2),
                "used_gb": round(memory_used_gb, 2),
                "percent_used": memory_percent,
                "process_usage_mb": round(process_memory_mb, 2)
            },
            "disk": {
                "free_gb": round(disk_free_gb, 2)
            },
            "gpu": gpu_info,
            "converter_recommendations": recommendations,
            "warnings": []
        }
        
        # Add warnings
        if memory_available_gb < 2.0:
            results["warnings"].append("⚠️ Very low memory! Even pymupdf4llm may struggle.")
        elif memory_available_gb < 4.0:
            results["warnings"].append("⚠️ Memory too low for marker-pdf. Use pymupdf4llm only.")
        
        if cpu_percent > 90:
            results["warnings"].append("⚠️ CPU is heavily loaded. Conversions will be slow.")
        
        if disk_free_gb < 1.0:
            results["warnings"].append("⚠️ Low disk space may affect paper downloads.")
        
        return [
            types.TextContent(
                type="text",
                text=json.dumps(results, indent=2)
            )
        ]
        
    except Exception as e:
        logger.error(f"Error getting system stats: {str(e)}")
        return [
            types.TextContent(
                type="text",
                text=json.dumps({
                    "status": "error",
                    "message": f"Error getting system stats: {str(e)}"
                })
            )
        ]


# Validation function
if __name__ == "__main__":
    import sys
    
    print("\n=== SYSTEM STATS TOOL VALIDATION ===")
    
    # List to track all validation failures
    all_validation_failures = []
    total_tests = 0
    
    # Test 1: Tool definition
    total_tests += 1
    print("\n1. Testing tool definition...")
    
    if system_stats_tool.name == "get_system_stats":
        print("   ✓ Tool name is correct")
    else:
        failure_msg = f"Tool name incorrect: {system_stats_tool.name}"
        all_validation_failures.append(failure_msg)
        print(f"   ✗ {failure_msg}")
    
    # Test 2: Get system stats
    total_tests += 1
    print("\n2. Testing system stats collection...")
    
    async def test_stats():
        result = await handle_system_stats({})
        return result
    
    try:
        result = asyncio.run(test_stats())
        if result and len(result) > 0:
            stats = json.loads(result[0].text)
            
            # Check response structure
            expected_keys = {"system", "cpu", "memory", "disk", "gpu", "converter_recommendations", "warnings"}
            if set(stats.keys()) >= expected_keys:
                print("   ✓ Response has correct structure")
                print(f"   ✓ CPU Usage: {stats['cpu']['usage_percent']}%")
                print(f"   ✓ Memory Available: {stats['memory']['available_gb']}GB")
                print(f"   ✓ Recommended Converter: {stats['converter_recommendations']['recommended_converter']}")
                print(f"   ✓ Can use marker-pdf: {stats['converter_recommendations']['can_use_marker']}")
                
                # Show warnings if any
                if stats['warnings']:
                    print("\n   Warnings:")
                    for warning in stats['warnings']:
                        print(f"   {warning}")
            else:
                failure_msg = f"Response missing keys: {expected_keys - set(stats.keys())}"
                all_validation_failures.append(failure_msg)
                print(f"   ✗ {failure_msg}")
        else:
            failure_msg = "Handle function returned empty result"
            all_validation_failures.append(failure_msg)
            print(f"   ✗ {failure_msg}")
            
    except Exception as e:
        failure_msg = f"System stats test failed: {e}"
        all_validation_failures.append(failure_msg)
        print(f"   ✗ {failure_msg}")
    
    # Test 3: Recommendation logic
    total_tests += 1
    print("\n3. Testing recommendation logic...")
    
    test_cases = [
        (20, 2.0, False, "Low memory"),  # Low memory
        (90, 8.0, False, "High CPU"),     # High CPU
        (30, 8.0, True, "Good resources"), # Good resources
        (60, 5.0, True, "Moderate"),       # Moderate
    ]
    
    all_passed = True
    for cpu, mem, expected_can_use, expected_reason in test_cases:
        rec = get_converter_recommendations(cpu, mem)
        if rec["can_use_marker"] == expected_can_use and expected_reason in rec["reasoning"]:
            print(f"   ✓ CPU:{cpu}%, RAM:{mem}GB → {rec['recommended_converter']} ({expected_reason})")
        else:
            all_passed = False
            print(f"   ✗ CPU:{cpu}%, RAM:{mem}GB → Unexpected: {rec}")
    
    if not all_passed:
        all_validation_failures.append("Recommendation logic test failed")
    
    # Final validation result
    print("\n=== VALIDATION SUMMARY ===")
    if all_validation_failures:
        print(f"❌ VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"✅ VALIDATION PASSED - All {total_tests} tests produced expected results")
        print("\nSystem stats tool features:")
        print("  - Real-time CPU and memory monitoring")
        print("  - Converter recommendations based on resources")
        print("  - GPU detection (if available)")
        print("  - Warning system for resource constraints")
        print("  - Helps agents make informed converter choices")
        sys.exit(0)