"""
Unit tests for GPU Manager

Tests GPU allocation, release, and management functionality.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio
from datetime import datetime

from opencode.core.gpu_manager import (
    GPUManager,
    GPUManagerConfig,
    GPUAllocation,
    GPUAllocationStrategy,
    get_gpu_manager,
    reset_gpu_manager,
)
from opencode.router.vram_monitor import VRAMStatus, GPUInfo, GPUVendor


@pytest.fixture
def gpu_manager():
    """Create a fresh GPU manager for each test."""
    reset_gpu_manager()
    manager = GPUManager()
    yield manager
    reset_gpu_manager()


@pytest.fixture
def mock_vram_status():
    """Create a mock VRAM status with 2 GPUs."""
    return VRAMStatus(
        gpus=[
            GPUInfo(
                index=0,
                name="RTX 4090",
                vendor=GPUVendor.NVIDIA,
                total_memory_mb=24564,
                used_memory_mb=8192,
                free_memory_mb=16372,
                utilization_percent=33.0,
                temperature_c=65.0,
            ),
            GPUInfo(
                index=1,
                name="RTX 3080",
                vendor=GPUVendor.NVIDIA,
                total_memory_mb=10240,
                used_memory_mb=2048,
                free_memory_mb=8192,
                utilization_percent=20.0,
                temperature_c=60.0,
            ),
        ],
        total_memory_mb=34804,
        total_used_mb=10240,
        total_free_mb=24564,
        timestamp=datetime.now(),
    )


class TestGPUManagerConfig:
    """Tests for GPUManagerConfig."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = GPUManagerConfig()
        assert config.strategy == GPUAllocationStrategy.AUTO
        assert config.vram_threshold_percent == 85.0
        assert config.allow_shared_gpu is True
        assert config.auto_unload is True
        assert config.reserved_vram_gb == 1.0
    
    def test_custom_config(self):
        """Test custom configuration values."""
        config = GPUManagerConfig(
            strategy=GPUAllocationStrategy.ROUND_ROBIN,
            vram_threshold_percent=90.0,
            allow_shared_gpu=False,
        )
        assert config.strategy == GPUAllocationStrategy.ROUND_ROBIN
        assert config.vram_threshold_percent == 90.0
        assert config.allow_shared_gpu is False


class TestGPUAllocation:
    """Tests for GPUAllocation dataclass."""
    
    def test_allocation_creation(self):
        """Test creating a GPU allocation."""
        alloc = GPUAllocation(
            gpu_id=0,
            model_id="llama3.2:70b",
            vram_required_gb=40.0,
        )
        assert alloc.gpu_id == 0
        assert alloc.model_id == "llama3.2:70b"
        assert alloc.vram_required_gb == 40.0
        assert alloc.exclusive is True
    
    def test_allocation_exclusive_flag(self):
        """Test exclusive flag."""
        alloc = GPUAllocation(
            gpu_id=1,
            model_id="mistral:7b",
            vram_required_gb=16.0,
            exclusive=False,
        )
        assert alloc.exclusive is False


class TestGPUManager:
    """Tests for GPUManager class."""
    
    @pytest.mark.asyncio
    async def test_get_available_gpus(self, gpu_manager, mock_vram_status):
        """Test getting available GPUs."""
        with patch.object(
            gpu_manager._vram_monitor,
            'get_status',
            new_callable=AsyncMock,
            return_value=mock_vram_status
        ):
            gpus = await gpu_manager.get_available_gpus()
            assert len(gpus) == 2
            assert gpus[0].name == "RTX 4090"
            assert gpus[1].name == "RTX 3080"
    
    @pytest.mark.asyncio
    async def test_allocate_gpu_auto_strategy(self, gpu_manager, mock_vram_status):
        """Test GPU allocation with auto strategy."""
        with patch.object(
            gpu_manager._vram_monitor,
            'get_status',
            new_callable=AsyncMock,
            return_value=mock_vram_status
        ):
            # Auto strategy should pick GPU with most free memory
            gpu_id = await gpu_manager.allocate_gpu(
                model_id="test_model",
                vram_required_gb=10.0,
            )
            assert gpu_id == 0  # RTX 4090 has more free memory
    
    @pytest.mark.asyncio
    async def test_allocate_gpu_preferred(self, gpu_manager, mock_vram_status):
        """Test GPU allocation with preferred GPU."""
        with patch.object(
            gpu_manager._vram_monitor,
            'get_status',
            new_callable=AsyncMock,
            return_value=mock_vram_status
        ):
            gpu_id = await gpu_manager.allocate_gpu(
                model_id="test_model",
                vram_required_gb=5.0,
                preferred_gpu_id=1,
            )
            assert gpu_id == 1
    
    @pytest.mark.asyncio
    async def test_allocate_gpu_insufficient_vram(self, gpu_manager, mock_vram_status):
        """Test allocation fails when VRAM is insufficient."""
        with patch.object(
            gpu_manager._vram_monitor,
            'get_status',
            new_callable=AsyncMock,
            return_value=mock_vram_status
        ):
            # Request more VRAM than available
            gpu_id = await gpu_manager.allocate_gpu(
                model_id="huge_model",
                vram_required_gb=100.0,  # More than any GPU has
            )
            assert gpu_id is None
    
    @pytest.mark.asyncio
    async def test_release_gpu(self, gpu_manager, mock_vram_status):
        """Test releasing GPU allocation."""
        with patch.object(
            gpu_manager._vram_monitor,
            'get_status',
            new_callable=AsyncMock,
            return_value=mock_vram_status
        ):
            # Allocate first
            gpu_id = await gpu_manager.allocate_gpu(
                model_id="test_model",
                vram_required_gb=10.0,
            )
            assert gpu_id is not None
            
            # Release
            released = await gpu_manager.release_gpu("test_model")
            assert released is True
            
            # Try to release again
            released = await gpu_manager.release_gpu("test_model")
            assert released is False
    
    @pytest.mark.asyncio
    async def test_release_all(self, gpu_manager, mock_vram_status):
        """Test releasing all allocations."""
        with patch.object(
            gpu_manager._vram_monitor,
            'get_status',
            new_callable=AsyncMock,
            return_value=mock_vram_status
        ):
            # Allocate multiple
            await gpu_manager.allocate_gpu("model1", 5.0)
            await gpu_manager.allocate_gpu("model2", 5.0)
            
            count = await gpu_manager.release_all()
            assert count == 2
    
    @pytest.mark.asyncio
    async def test_get_gpu_for_model(self, gpu_manager, mock_vram_status):
        """Test getting GPU ID for a model."""
        with patch.object(
            gpu_manager._vram_monitor,
            'get_status',
            new_callable=AsyncMock,
            return_value=mock_vram_status
        ):
            await gpu_manager.allocate_gpu("test_model", 10.0)
            
            gpu_id = await gpu_manager.get_gpu_for_model("test_model")
            assert gpu_id is not None
            
            gpu_id = await gpu_manager.get_gpu_for_model("unknown_model")
            assert gpu_id is None
    
    @pytest.mark.asyncio
    async def test_get_models_on_gpu(self, gpu_manager, mock_vram_status):
        """Test getting models on a specific GPU."""
        with patch.object(
            gpu_manager._vram_monitor,
            'get_status',
            new_callable=AsyncMock,
            return_value=mock_vram_status
        ):
            await gpu_manager.allocate_gpu("model1", 5.0, preferred_gpu_id=0)
            await gpu_manager.allocate_gpu("model2", 5.0, preferred_gpu_id=0)
            
            models = await gpu_manager.get_models_on_gpu(0)
            assert "model1" in models
            assert "model2" in models
            
            models = await gpu_manager.get_models_on_gpu(1)
            assert len(models) == 0
    
    @pytest.mark.asyncio
    async def test_get_status(self, gpu_manager, mock_vram_status):
        """Test getting GPU manager status."""
        with patch.object(
            gpu_manager._vram_monitor,
            'get_status',
            new_callable=AsyncMock,
            return_value=mock_vram_status
        ):
            await gpu_manager.allocate_gpu("test_model", 10.0)
            
            status = await gpu_manager.get_status()
            assert "gpus" in status
            assert "allocations" in status
            assert "strategy" in status
            assert len(status["gpus"]) == 2
            assert "test_model" in status["allocations"]
    
    @pytest.mark.asyncio
    async def test_recommend_allocation(self, gpu_manager, mock_vram_status):
        """Test GPU allocation recommendations."""
        with patch.object(
            gpu_manager._vram_monitor,
            'get_status',
            new_callable=AsyncMock,
            return_value=mock_vram_status
        ):
            models = [
                {"model_id": "model1", "vram_required_gb": 10.0},
                {"model_id": "model2", "vram_required_gb": 5.0},
            ]
            
            recommendations = await gpu_manager.recommend_allocation(models)
            assert "model1" in recommendations
            assert "model2" in recommendations
    
    @pytest.mark.asyncio
    async def test_can_run_parallel(self, gpu_manager, mock_vram_status):
        """Test checking if models can run in parallel."""
        with patch.object(
            gpu_manager._vram_monitor,
            'get_status',
            new_callable=AsyncMock,
            return_value=mock_vram_status
        ):
            # Should fit on 2 GPUs
            models = [
                {"model_id": "model1", "vram_required_gb": 10.0},
                {"model_id": "model2", "vram_required_gb": 5.0},
            ]
            
            can_run = await gpu_manager.can_run_parallel(models)
            assert can_run is True
            
            # Should not fit
            models_huge = [
                {"model_id": "huge1", "vram_required_gb": 50.0},
                {"model_id": "huge2", "vram_required_gb": 50.0},
            ]
            
            can_run = await gpu_manager.can_run_parallel(models_huge)
            assert can_run is False
    
    @pytest.mark.asyncio
    async def test_round_robin_strategy(self, mock_vram_status):
        """Test round-robin allocation strategy."""
        config = GPUManagerConfig(strategy=GPUAllocationStrategy.ROUND_ROBIN)
        manager = GPUManager(config)
        
        with patch.object(
            manager._vram_monitor,
            'get_status',
            new_callable=AsyncMock,
            return_value=mock_vram_status
        ):
            # Allocate multiple models
            gpu1 = await manager.allocate_gpu("model1", 5.0)
            gpu2 = await manager.allocate_gpu("model2", 5.0)
            
            # Should distribute across GPUs
            # Note: exact distribution depends on implementation
            assert gpu1 is not None
            assert gpu2 is not None
    
    @pytest.mark.asyncio
    async def test_pack_strategy(self, mock_vram_status):
        """Test pack allocation strategy."""
        config = GPUManagerConfig(strategy=GPUAllocationStrategy.PACK)
        manager = GPUManager(config)
        
        with patch.object(
            manager._vram_monitor,
            'get_status',
            new_callable=AsyncMock,
            return_value=mock_vram_status
        ):
            # Pack should fill GPU 0 first
            gpu1 = await manager.allocate_gpu("model1", 5.0)
            assert gpu1 == 0  # Should be GPU 0
    
    @pytest.mark.asyncio
    async def test_spread_strategy(self, mock_vram_status):
        """Test spread allocation strategy."""
        config = GPUManagerConfig(strategy=GPUAllocationStrategy.SPREAD)
        manager = GPUManager(config)
        
        with patch.object(
            manager._vram_monitor,
            'get_status',
            new_callable=AsyncMock,
            return_value=mock_vram_status
        ):
            # Spread should use least utilized GPU
            gpu1 = await manager.allocate_gpu("model1", 5.0)
            # GPU 1 has lower utilization (20% vs 33%)
            assert gpu1 == 1
    
    @pytest.mark.asyncio
    async def test_exclusive_allocation(self, gpu_manager, mock_vram_status):
        """Test exclusive GPU allocation."""
        with patch.object(
            gpu_manager._vram_monitor,
            'get_status',
            new_callable=AsyncMock,
            return_value=mock_vram_status
        ):
            # Allocate with exclusive flag
            gpu1 = await gpu_manager.allocate_gpu(
                "exclusive_model",
                5.0,
                preferred_gpu_id=0,
                exclusive=True,
            )
            assert gpu1 == 0
            
            # Try to allocate another on same GPU
            gpu2 = await gpu_manager.allocate_gpu(
                "another_model",
                5.0,
                preferred_gpu_id=0,
            )
            # Should fail because GPU 0 is exclusive
            assert gpu2 != 0  # Should get different GPU or None
    
    @pytest.mark.asyncio
    async def test_shared_gpu_disabled(self, mock_vram_status):
        """Test with shared GPU disabled."""
        config = GPUManagerConfig(allow_shared_gpu=False)
        manager = GPUManager(config)
        
        with patch.object(
            manager._vram_monitor,
            'get_status',
            new_callable=AsyncMock,
            return_value=mock_vram_status
        ):
            # Allocate first model
            gpu1 = await manager.allocate_gpu("model1", 5.0)
            assert gpu1 is not None
            
            # Try to allocate another model
            gpu2 = await manager.allocate_gpu("model2", 5.0)
            # Should get different GPU since sharing is disabled
            if gpu2 is not None:
                assert gpu2 != gpu1
    
    @pytest.mark.asyncio
    async def test_already_allocated(self, gpu_manager, mock_vram_status):
        """Test allocating already allocated model."""
        with patch.object(
            gpu_manager._vram_monitor,
            'get_status',
            new_callable=AsyncMock,
            return_value=mock_vram_status
        ):
            gpu1 = await gpu_manager.allocate_gpu("model1", 5.0)
            gpu2 = await gpu_manager.allocate_gpu("model1", 5.0)
            
            # Should return same allocation
            assert gpu1 == gpu2


class TestGetGPUManager:
    """Tests for global GPU manager functions."""
    
    def test_get_gpu_manager_singleton(self):
        """Test that get_gpu_manager returns singleton."""
        reset_gpu_manager()
        manager1 = get_gpu_manager()
        manager2 = get_gpu_manager()
        assert manager1 is manager2
        reset_gpu_manager()
    
    def test_reset_gpu_manager(self):
        """Test resetting GPU manager."""
        manager1 = get_gpu_manager()
        reset_gpu_manager()
        manager2 = get_gpu_manager()
        assert manager1 is not manager2


class TestGPUAllocationStrategy:
    """Tests for GPUAllocationStrategy enum."""
    
    def test_strategy_values(self):
        """Test strategy enum values."""
        assert GPUAllocationStrategy.AUTO.value == "auto"
        assert GPUAllocationStrategy.ROUND_ROBIN.value == "round_robin"
        assert GPUAllocationStrategy.PACK.value == "pack"
        assert GPUAllocationStrategy.SPREAD.value == "spread"
        assert GPUAllocationStrategy.MANUAL.value == "manual"
