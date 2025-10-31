"""
Tor Pool Service - Manages Tor instances
"""
import asyncio
import logging
import os
import subprocess
from typing import List, Optional, Dict
from datetime import datetime
from pathlib import Path

import stem
from stem.control import Controller
from prometheus_client import Gauge, Counter

from app.core.config import settings
from app.services.metrics import (
    tor_nodes_total,
    tor_nodes_up,
    tor_node_latency,
    tor_newnym_total,
    tor_restarts_total
)

logger = logging.getLogger(__name__)


class TorInstance:
    """Represents a single Tor instance"""
    
    def __init__(self, node_id: str, socks_port: int, control_port: int, data_dir: str):
        self.node_id = node_id
        self.socks_port = socks_port
        self.control_port = control_port
        self.data_dir = data_dir
        self.process = None
        self.exit_ip = None
        self.exit_country = None
        self.is_healthy = False
        self.controller = None
    
    async def start(self):
        """Start the Tor instance"""
        try:
            # Create data directory
            Path(self.data_dir).mkdir(parents=True, exist_ok=True)
            
            # Generate torrc config
            torrc_path = os.path.join(self.data_dir, "torrc")
            self._generate_torrc(torrc_path)
            
            # Start Tor process
            cmd = [
                "tor",
                "-f", torrc_path,
                "--DataDirectory", self.data_dir,
                "--SocksPort", str(self.socks_port),
                "--ControlPort", str(self.control_port),
            ]
            
            self.process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Wait for Tor to bootstrap
            await self._wait_for_bootstrap()
            
            logger.info(f"Tor instance {self.node_id} started on ports SOCKS:{self.socks_port} CTRL:{self.control_port}")
            
            # Update metrics
            tor_nodes_up.inc()
            
        except Exception as e:
            logger.error(f"Failed to start Tor instance {self.node_id}: {e}")
            raise
    
    def _generate_torrc(self, path: str):
        """Generate torrc configuration file"""
        config_lines = [
            f"SocksPort 127.0.0.1:{self.socks_port}",
            f"ControlPort 127.0.0.1:{self.control_port}",
            f"DataDirectory {self.data_dir}",
            "CookieAuthentication 1",
            "CircuitBuildTimeout 30",
            "LearnCircuitBuildTimeout 0",
            "MaxCircuitDirtiness 600",
        ]
        
        # Add country restrictions if configured
        if settings.TOR_COUNTRIES:
            countries = ",".join([f"{{{c}}}" for c in settings.TOR_COUNTRIES])
            config_lines.append(f"ExitNodes {countries}")
            if settings.TOR_STRICT_NODES:
                config_lines.append("StrictNodes 1")
        
        with open(path, 'w') as f:
            f.write('\n'.join(config_lines))
    
    async def _wait_for_bootstrap(self, timeout: int = 60):
        """Wait for Tor to bootstrap"""
        start_time = asyncio.get_event_loop().time()
        
        while asyncio.get_event_loop().time() - start_time < timeout:
            try:
                async with Controller.from_port(port=self.control_port) as controller:
                    await controller.authenticate()
                    bootstrap_status = await controller.get_info("status/bootstrap-phase")
                    
                    if "PROGRESS=100" in bootstrap_status:
                        self.is_healthy = True
                        return
                    
            except Exception:
                pass
            
            await asyncio.sleep(1)
        
        raise TimeoutError(f"Tor instance {self.node_id} failed to bootstrap within {timeout}s")
    
    async def newnym(self):
        """Request new Tor circuit (NEWNYM signal)"""
        try:
            with Controller.from_port(port=self.control_port) as controller:
                controller.authenticate()
                controller.signal(stem.Signal.NEWNYM)
                
                logger.info(f"NEWNYM sent to {self.node_id}")
                tor_newnym_total.labels(node_id=self.node_id).inc()
                
                # Wait a bit for new circuit
                await asyncio.sleep(2)
                
                # Update exit IP
                await self.update_exit_info()
                
        except Exception as e:
            logger.error(f"Failed to send NEWNYM to {self.node_id}: {e}")
            raise
    
    async def update_exit_info(self):
        """Update exit IP and country information"""
        # This would normally query through the SOCKS proxy to get exit IP
        # Simplified for now
        pass
    
    async def check_health(self) -> bool:
        """Check if Tor instance is healthy"""
        try:
            with Controller.from_port(port=self.control_port) as controller:
                controller.authenticate()
                circuit_status = controller.get_info("circuit-status")
                self.is_healthy = circuit_status is not None
                return self.is_healthy
        except Exception as e:
            logger.warning(f"Health check failed for {self.node_id}: {e}")
            self.is_healthy = False
            return False
    
    async def stop(self):
        """Stop the Tor instance"""
        try:
            if self.process:
                self.process.terminate()
                await self.process.wait()
                logger.info(f"Tor instance {self.node_id} stopped")
                
                # Update metrics
                tor_nodes_up.dec()
                
        except Exception as e:
            logger.error(f"Failed to stop Tor instance {self.node_id}: {e}")


class TorPoolService:
    """Manages pool of Tor instances"""
    
    def __init__(self):
        self.instances: Dict[str, TorInstance] = {}
        self.health_check_task = None
        self.rotation_task = None
    
    async def initialize(self, pool_size: int):
        """Initialize Tor pool with specified size"""
        logger.info(f"Initializing Tor pool with {pool_size} instances")
        
        # Update metrics
        tor_nodes_total.set(pool_size)
        
        # Create instances
        tasks = []
        for i in range(pool_size):
            node_id = f"tor-{i:04d}"
            socks_port = settings.TOR_BASE_SOCKS_PORT + i
            control_port = settings.TOR_BASE_CTRL_PORT + i
            data_dir = os.path.join(settings.TOR_DATA_DIR, node_id)
            
            instance = TorInstance(node_id, socks_port, control_port, data_dir)
            self.instances[node_id] = instance
            
            # Start instance (parallel)
            tasks.append(instance.start())
        
        # Wait for all instances to start
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Log results
        success_count = sum(1 for r in results if not isinstance(r, Exception))
        logger.info(f"Started {success_count}/{pool_size} Tor instances successfully")
        
        # Start background tasks
        self.health_check_task = asyncio.create_task(self._health_check_loop())
        
        if settings.AUTO_ROTATE_ENABLED:
            self.rotation_task = asyncio.create_task(self._rotation_loop())
    
    async def scale(self, new_size: int):
        """Scale pool to new size"""
        current_size = len(self.instances)
        
        if new_size > current_size:
            # Scale up
            logger.info(f"Scaling up from {current_size} to {new_size}")
            
            for i in range(current_size, new_size):
                node_id = f"tor-{i:04d}"
                socks_port = settings.TOR_BASE_SOCKS_PORT + i
                control_port = settings.TOR_BASE_CTRL_PORT + i
                data_dir = os.path.join(settings.TOR_DATA_DIR, node_id)
                
                instance = TorInstance(node_id, socks_port, control_port, data_dir)
                await instance.start()
                self.instances[node_id] = instance
            
            tor_nodes_total.set(new_size)
            
        elif new_size < current_size:
            # Scale down
            logger.info(f"Scaling down from {current_size} to {new_size}")
            
            nodes_to_remove = list(self.instances.keys())[new_size:]
            
            for node_id in nodes_to_remove:
                instance = self.instances[node_id]
                await instance.stop()
                del self.instances[node_id]
            
            tor_nodes_total.set(new_size)
    
    async def rotate_all(self):
        """Rotate all Tor circuits"""
        logger.info("Rotating all Tor circuits")
        
        tasks = [instance.newnym() for instance in self.instances.values()]
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def rotate_node(self, node_id: str):
        """Rotate specific Tor node"""
        if node_id in self.instances:
            await self.instances[node_id].newnym()
        else:
            raise ValueError(f"Node {node_id} not found")
    
    async def get_node_status(self, node_id: str) -> Dict:
        """Get status of specific node"""
        if node_id not in self.instances:
            raise ValueError(f"Node {node_id} not found")
        
        instance = self.instances[node_id]
        return {
            "node_id": instance.node_id,
            "socks_port": instance.socks_port,
            "control_port": instance.control_port,
            "is_healthy": instance.is_healthy,
            "exit_ip": instance.exit_ip,
            "exit_country": instance.exit_country,
        }
    
    async def get_all_status(self) -> List[Dict]:
        """Get status of all nodes"""
        return [await self.get_node_status(node_id) for node_id in self.instances.keys()]
    
    async def _health_check_loop(self):
        """Background task for health checking"""
        while True:
            try:
                await asyncio.sleep(settings.HEALTH_CHECK_INTERVAL)
                
                logger.debug("Running health checks on all nodes")
                
                for instance in self.instances.values():
                    await instance.check_health()
                
                # Update metrics
                healthy_count = sum(1 for i in self.instances.values() if i.is_healthy)
                tor_nodes_up.set(healthy_count)
                
            except Exception as e:
                logger.error(f"Health check loop error: {e}")
    
    async def _rotation_loop(self):
        """Background task for automatic rotation"""
        while True:
            try:
                await asyncio.sleep(settings.AUTO_ROTATE_INTERVAL)
                
                logger.info("Auto-rotating all circuits")
                await self.rotate_all()
                
            except Exception as e:
                logger.error(f"Rotation loop error: {e}")
    
    async def shutdown(self):
        """Shutdown all Tor instances"""
        logger.info("Shutting down Tor pool")
        
        # Cancel background tasks
        if self.health_check_task:
            self.health_check_task.cancel()
        if self.rotation_task:
            self.rotation_task.cancel()
        
        # Stop all instances
        tasks = [instance.stop() for instance in self.instances.values()]
        await asyncio.gather(*tasks, return_exceptions=True)
        
        logger.info("Tor pool shutdown complete")
