import asyncio
import logging
import tempfile
import os
import re
import signal
import subprocess
from typing import Optional
from app.core.config import get_settings
from .connection import CDPConnection

logger = logging.getLogger(__name__)

class ChromeLauncher:
    """Chrome process launcher with CDP support"""
    
    def __init__(self):
        self.settings = get_settings()
        self.process: Optional[subprocess.Popen] = None
        self.user_data_dir: Optional[str] = None
        self.connection: Optional[CDPConnection] = None
        
    async def launch(self, headless: bool = True) -> CDPConnection:
        """Launch Chrome process
        
        Args:
            headless: Whether to run in headless mode
            
        Returns:
            CDP connection to browser
        """
        # Create temporary user data directory
        self.user_data_dir = tempfile.mkdtemp()
        
        # Prepare Chrome arguments
        args = [
            self.settings.chrome_binary_path,
            f"--user-data-dir={self.user_data_dir}",
            "--remote-debugging-port=0",  # Let Chrome pick a port
            "--no-first-run",
            "--no-default-browser-check",
        ]
        
        if headless:
            args.extend([
                "--headless=new",
                "--hide-scrollbars",
                "--mute-audio"
            ])
            
        # Add any custom arguments
        args.extend(self.settings.chrome_args or [])
        
        try:
            # Start Chrome process
            self.process = subprocess.Popen(
                args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid  # Create new process group
            )
            
            # Get WebSocket URL from stderr
            ws_url = await self._get_ws_url()
            if not ws_url:
                raise Exception("Failed to get WebSocket URL from Chrome")
                
            # Create CDP connection
            self.connection = CDPConnection(ws_url)
            if not await self.connection.connect():
                raise Exception("Failed to connect to Chrome")
                
            return self.connection
            
        except Exception as e:
            await self.cleanup()
            raise Exception(f"Failed to launch Chrome: {str(e)}")
            
    async def cleanup(self):
        """Clean up Chrome process and temporary files"""
        if self.connection:
            await self.connection.disconnect()
            self.connection = None
            
        if self.process:
            try:
                # Kill process group
                os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
                self.process.wait(timeout=5)
            except:
                # Force kill if needed
                try:
                    os.killpg(os.getpgid(self.process.pid), signal.SIGKILL)
                except:
                    pass
            self.process = None
            
        if self.user_data_dir:
            try:
                import shutil
                shutil.rmtree(self.user_data_dir)
            except:
                pass
            self.user_data_dir = None
            
    async def _get_ws_url(self, timeout: float = 30) -> Optional[str]:
        """Get WebSocket URL from Chrome stderr
        
        Args:
            timeout: Timeout in seconds
            
        Returns:
            WebSocket URL or None if not found
        """
        if not self.process:
            return None
            
        pattern = rb"DevTools listening on (ws://.*)"
        start_time = asyncio.get_event_loop().time()
        
        while asyncio.get_event_loop().time() - start_time < timeout:
            line = self.process.stderr.readline()
            if not line:
                continue
                
            match = re.search(pattern, line)
            if match:
                return match.group(1).decode()
                
            # Check if process died
            if self.process.poll() is not None:
                raise Exception(f"Chrome died: {self.process.returncode}")
                
            await asyncio.sleep(0.1)
            
        return None
