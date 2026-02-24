"""
Data Source Node

Handles file, JSON, and text data input for workflows.
"""

import json
import os
from typing import Any, Dict, Optional
import logging

from opencode.workflow.node import (
    BaseNode,
    NodePort,
    NodeSchema,
    ExecutionContext,
    ExecutionResult,
    PortDataType,
    PortDirection,
)
from opencode.workflow.registry import NodeRegistry

logger = logging.getLogger(__name__)


class SourceType:
    """Supported source types for DataSourceNode."""
    FILE = "file"
    JSON = "json"
    TEXT = "text"
    URL = "url"


@NodeRegistry.register("data_source")
class DataSourceNode(BaseNode):
    """
    Data Source Node - Handles file, JSON, and text data input.
    
    This node provides data to the workflow from various sources:
    - File: Read from a file path
    - JSON: Parse inline JSON data
    - Text: Use inline text data
    - URL: Fetch data from a URL
    
    Configuration:
        sourceType: Type of data source (file, json, text, url)
        filePath: Path to file (for file source)
        jsonData: Inline JSON string (for json source)
        textData: Inline text (for text source)
        url: URL to fetch (for url source)
        encoding: File encoding (default: utf-8)
    """
    
    _schema = NodeSchema(
        node_type="data_source",
        display_name="Data Source",
        description="Provides data to the workflow from files, JSON, text, or URLs",
        category="input",
        icon="database",
        inputs=[
            NodePort(
                name="trigger",
                data_type=PortDataType.ANY,
                direction=PortDirection.INPUT,
                required=False,
                description="Optional trigger input to start data loading",
            ),
        ],
        outputs=[
            NodePort(
                name="data",
                data_type=PortDataType.ANY,
                direction=PortDirection.OUTPUT,
                required=True,
                description="The loaded data",
            ),
            NodePort(
                name="raw",
                data_type=PortDataType.STRING,
                direction=PortDirection.OUTPUT,
                required=False,
                description="Raw string data before parsing",
            ),
        ],
        config_schema={
            "type": "object",
            "properties": {
                "sourceType": {
                    "type": "string",
                    "enum": ["file", "json", "text", "url"],
                    "default": "text",
                    "description": "Type of data source",
                },
                "filePath": {
                    "type": "string",
                    "description": "Path to file for file source type",
                },
                "jsonData": {
                    "type": "string",
                    "description": "Inline JSON data for json source type",
                },
                "textData": {
                    "type": "string",
                    "description": "Inline text data for text source type",
                },
                "url": {
                    "type": "string",
                    "description": "URL to fetch for url source type",
                },
                "encoding": {
                    "type": "string",
                    "default": "utf-8",
                    "description": "File encoding for file source type",
                },
            },
            "required": ["sourceType"],
        },
        version="1.0.0",
    )
    
    @classmethod
    def get_schema(cls) -> NodeSchema:
        return cls._schema
    
    async def execute(
        self,
        inputs: Dict[str, Any],
        context: ExecutionContext,
    ) -> ExecutionResult:
        """Execute the data source node."""
        import time
        start_time = time.time()
        
        try:
            source_type = self.config.get("sourceType", "text")
            
            if source_type == SourceType.FILE:
                result = await self._handle_file_source()
            elif source_type == SourceType.JSON:
                result = await self._handle_json_source()
            elif source_type == SourceType.TEXT:
                result = await self._handle_text_source()
            elif source_type == SourceType.URL:
                result = await self._handle_url_source()
            else:
                return ExecutionResult(
                    success=False,
                    error=f"Unknown source type: {source_type}",
                )
            
            duration_ms = (time.time() - start_time) * 1000
            result.duration_ms = duration_ms
            return result
            
        except Exception as e:
            logger.exception(f"Data source execution failed: {e}")
            return ExecutionResult(
                success=False,
                error=str(e),
                error_traceback=str(e.__traceback__),
            )
    
    async def _handle_file_source(self) -> ExecutionResult:
        """Handle file source type."""
        file_path = self.config.get("filePath")
        if not file_path:
            return ExecutionResult(
                success=False,
                error="filePath is required for file source type",
            )
        
        encoding = self.config.get("encoding", "utf-8")
        
        # Check if file exists
        if not os.path.exists(file_path):
            return ExecutionResult(
                success=False,
                error=f"File not found: {file_path}",
            )
        
        try:
            with open(file_path, "r", encoding=encoding) as f:
                raw_data = f.read()
            
            # Try to parse as JSON
            try:
                data = json.loads(raw_data)
            except json.JSONDecodeError:
                data = raw_data
            
            return ExecutionResult(
                success=True,
                outputs={"data": data, "raw": raw_data},
            )
        except IOError as e:
            return ExecutionResult(
                success=False,
                error=f"Error reading file: {e}",
            )
    
    async def _handle_json_source(self) -> ExecutionResult:
        """Handle JSON source type."""
        json_data = self.config.get("jsonData")
        if not json_data:
            return ExecutionResult(
                success=False,
                error="jsonData is required for json source type",
            )
        
        try:
            data = json.loads(json_data)
            return ExecutionResult(
                success=True,
                outputs={"data": data, "raw": json_data},
            )
        except json.JSONDecodeError as e:
            return ExecutionResult(
                success=False,
                error=f"Invalid JSON: {e}",
            )
    
    async def _handle_text_source(self) -> ExecutionResult:
        """Handle text source type."""
        text_data = self.config.get("textData", "")
        
        return ExecutionResult(
            success=True,
            outputs={"data": text_data, "raw": text_data},
        )
    
    async def _handle_url_source(self) -> ExecutionResult:
        """Handle URL source type."""
        url = self.config.get("url")
        if not url:
            return ExecutionResult(
                success=False,
                error="url is required for url source type",
            )
        
        try:
            import httpx
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, follow_redirects=True)
                response.raise_for_status()
                
                raw_data = response.text
                
                # Try to parse as JSON
                try:
                    data = json.loads(raw_data)
                except json.JSONDecodeError:
                    data = raw_data
                
                return ExecutionResult(
                    success=True,
                    outputs={"data": data, "raw": raw_data},
                )
        except ImportError:
            return ExecutionResult(
                success=False,
                error="httpx is required for URL source type. Install with: pip install httpx",
            )
        except Exception as e:
            return ExecutionResult(
                success=False,
                error=f"Error fetching URL: {e}",
            )
