import pytest
from fastapi.testclient import TestClient
from backend.edge_optimizer import EdgeOptimizer, HARDWARE_PROFILES
from backend.api import AnalyticalBackend
from backend.server import app

def test_edge_optimizer_supported_hardware():
    opt = EdgeOptimizer()
    hardware_list = opt.get_supported_hardware()
    assert "NVIDIA Jetson Orin Nano" in hardware_list
    assert "Raspberry Pi 5" in hardware_list
    assert "PX4 Companion Computer" in hardware_list

def test_edge_optimizer_benchmark():
    opt = EdgeOptimizer()
    for dev in opt.get_supported_hardware():
        bm = opt.benchmark_hardware(dev)
        assert bm["target_device"] == dev
        assert bm["latency_ms"] <= 6.0
        assert bm["ram_footprint_mb"] <= 10.0
        assert bm["throughput_fps"] >= 100
        assert bm["status"] == "OPTIMAL"

def test_edge_optimizer_onnx_export():
    opt = EdgeOptimizer()
    exp = opt.export_onnx_model("twinaero_pinn_diagnostic")
    assert exp["success"] is True
    assert exp["filename"] == "twinaero_pinn_diagnostic_int8.onnx"
    assert "payload_base64" in exp
    assert exp["byte_size_kb"] > 0

def test_analytical_backend_edge_integration():
    backend = AnalyticalBackend()
    bm = backend.get_edge_benchmark("NVIDIA Jetson Orin Nano")
    assert bm["target_device"] == "NVIDIA Jetson Orin Nano"
    assert bm["latency_ms"] <= 2.5
    
    exp = backend.export_onnx_model()
    assert exp["success"] is True

def test_api_server_edge_endpoints():
    client = TestClient(app)
    
    res_bm = client.get("/api/edge-benchmark?target_device=Raspberry%20Pi%205")
    assert res_bm.status_code == 200
    data_bm = res_bm.json()
    assert data_bm["target_device"] == "Raspberry Pi 5"
    assert "latency_ms" in data_bm
    
    res_exp = client.post("/api/edge-export-onnx")
    assert res_exp.status_code == 200
    data_exp = res_exp.json()
    assert data_exp["success"] is True
    assert "payload_base64" in data_exp
