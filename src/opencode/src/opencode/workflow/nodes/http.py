"""
HTTP Node

Handles HTTP/GraphQL requests for workflows.
"""

import json
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


@NodeRegistry.register("http")
class HttpNode(BaseNode):
    """
    HTTP Node - Handles HTTP/GraphQL requests.
    
    This node makes HTTP requests and returns the response data.
    Supports various HTTP methods, custom headers, and request bodies.
    
    Configuration:
        method: HTTP method (GET, POST, PUT, DELETE, PATCH)
        url: Request URL (supports template substitution)
        headers: Request headers
        bodyType: Type of request body (json, form, raw)
        body: Request body content
        timeout: Request timeout in seconds
        followRedirects: Whether to follow redirects
    """
    
    _schema = NodeSchema(
        node_type="http",
        display_name="HTTP Request",
        description="Make HTTP requests to external APIs",
        category="network",
        icon="globe",
        inputs=[
            NodePort(
                name="url",
                data_type=PortDataType.STRING,
                direction=PortDirection.INPUT,
                required=False,
                description="Override URL from config",
            ),
            NodePort(
                name="body",
                data_type=PortDataType.ANY,
                direction=PortDirection.INPUT,
                required=False,
                description="Request body data",
            ),
            NodePort(
                name="headers",
                data_type=PortDataType.OBJECT,
                direction=PortDirection.INPUT,
                required=False,
                description="Additional headers",
            ),
            NodePort(
                name="params",
                data_type=PortDataType.OBJECT,
                direction=PortDirection.INPUT,
                required=False,
                description="Query parameters",
            ),
        ],
        outputs=[
            NodePort(
                name="response",
                data_type=PortDataType.ANY,
                direction=PortDirection.OUTPUT,
                required=True,
                description="Response body (parsed JSON or raw text)",
            ),
            NodePort(
                name="status",
                data_type=PortDataType.INTEGER,
                direction=PortDirection.OUTPUT,
                required=True,
                description="HTTP status code",
            ),
            NodePort(
                name="headers",
                data_type=PortDataType.OBJECT,
                direction=PortDirection.OUTPUT,
                required=False,
                description="Response headers",
            ),
            NodePort(
                name="raw",
                data_type=PortDataType.STRING,
                direction=PortDirection.OUTPUT,
                required=False,
                description="Raw response text",
            ),
        ],
        config_schema={
            "type": "object",
            "properties": {
                "method": {
                    "type": "string",
                    "enum": ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"],
                    "default": "GET",
                    "description": "HTTP method",
                },
                "url": {
                    "type": "string",
                    "description": "Request URL",
                },
                "headers": {
                    "type": "object",
                    "description": "Request headers",
                },
                "bodyType": {
                    "type": "string",
                    "enum": ["json", "form", "raw", "none"],
                    "default": "json",
                    "description": "Type of request body",
                },
                "body": {
                    "type": ["string", "object"],
                    "description": "Request body content",
                },
                "timeout": {
                    "type": "integer",
                    "default": 30,
                    "description": "Request timeout in seconds",
                },
                "followRedirects": {
                    "type": "boolean",
                    "default": True,
                    "description": "Whether to follow redirects",
                },
            },
            "required": ["url"],
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
        """Execute the HTTP request node."""
        import time
        start_time = time.time()
        
        try:
            import httpx
        except ImportError:
            return ExecutionResult(
                success=False,
                error="httpx is required for HTTP requests. Install with: pip install httpx",
            )
        
        try:
            # Get request parameters
            method = self.config.get("method", "GET").upper()
            url = inputs.get("url") or self.config.get("url")
            
            if not url:
                return ExecutionResult(
                    success=False,
                    error="URL is required",
                )
            
            # Build headers
            headers = dict(self.config.get("headers", {}))
            if inputs.get("headers"):
                headers.update(inputs["headers"])
            
            # Build query parameters
            params = inputs.get("params")
            
            # Build request body
            body_data = inputs.get("body") or self.config.get("body")
            body_type = self.config.get("bodyType", "json")
            
            request_kwargs = {
                "method": method,
                "url": url,
                "headers": headers,
                "params": params,
                "follow_redirects": self.config.get("followRedirects", True),
                "timeout": self.config.get("timeout", 30),
            }
            
            if method not in ("GET", "HEAD") and body_data is not None:
                if body_type == "json":
                    request_kwargs["json"] = body_data
                elif body_type == "form":
                    request_kwargs["data"] = body_data
                elif body_type == "raw":
                    request_kwargs["content"] = body_data if isinstance(body_data, (str, bytes)) else str(body_data)
            
            # Make the request
            async with httpx.AsyncClient() as client:
                response = await client.request(**request_kwargs)
            
            # Parse response
            raw_text = response.text
            
            # Try to parse as JSON
            try:
                response_data = response.json()
            except (json.JSONDecodeError, ValueError):
                response_data = raw_text
            
            # Build outputs
            outputs = {
                "response": response_data,
                "status": response.status_code,
                "headers": dict(response.headers),
                "raw": raw_text,
            }
            
            duration_ms = (time.time() - start_time) * 1000
            return ExecutionResult(
                success=True,
                outputs=outputs,
                duration_ms=duration_ms,
            )
            
        except httpx.TimeoutException:
            return ExecutionResult(
                success=False,
                error=f"Request timed out after {self.config.get('timeout', 30)} seconds",
            )
        except httpx.RequestError as e:
            return ExecutionResult(
                success=False,
                error=f"Request error: {e}",
            )
        except Exception as e:
            logger.exception(f"HTTP request failed: {e}")
            return ExecutionResult(
                success=False,
                error=str(e),
            )
