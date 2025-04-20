# AST (Abstract Syntax Tree) Analysis for Pandora's Shell

This document contains the AST for the main `executor.py` file, which is the core of Pandora's Shell.

```python
import os
import subprocess
import asyncio
import re
import ipaddress
import logging
import shlex
from typing import List, Optional, Dict, Any, Union
from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
import mcp.server.stdio
import dotenv
from pathlib import Path

# Load environment variables from .env file
dotenv.load_dotenv(dotenv_path=Path(__file__).parent.parent.parent / ".env")

# Configure logging
logging.basicConfig(
    filename='itmcp.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('itmcp')

# Docker execution configuration
USE_DOCKER = os.environ.get("USE_DOCKER", "true").lower() == "true"
DOCKER_CONTAINER = os.environ.get("DOCKER_CONTAINER", "itmcp_container")
logger.info(f"Docker execution: {'Enabled' if USE_DOCKER else 'Disabled'}")
logger.info(f"Docker container: {DOCKER_CONTAINER if USE_DOCKER else 'N/A'}")

# Load whitelist configurations from environment variables
def get_list_from_env(env_var_name: str, default: List[str] = None) -> List[str]:
    """Parse comma-separated environment variable into a list."""
    value = os.environ.get(env_var_name, "")
    if not value and default is not None:
        return default
    return [item.strip() for item in value.split(",") if item.strip()]

# Load whitelist configurations
ALLOWED_HOSTS = get_list_from_env("ALLOWED_HOSTS", ["localhost", "127.0.0.1"])
ALLOWED_DIRECTORIES = get_list_from_env("ALLOWED_DIRECTORIES", ["/tmp"])
ALLOWED_REMOTE_COMMANDS = get_list_from_env("ALLOWED_REMOTE_COMMANDS", ["ls", "cat"])

# Log loaded configurations
logger.info(f"Loaded {len(ALLOWED_HOSTS)} allowed hosts")
logger.info(f"Loaded {len(ALLOWED_DIRECTORIES)} allowed directories")
logger.info(f"Loaded {len(ALLOWED_REMOTE_COMMANDS)} allowed remote commands")

server = Server("itmcp")

Module(
  body=[
    Import(
      names=[
        alias(name='os')]),
    Import(
      names=[
        alias(name='subprocess')]),
    Import(
      names=[
        alias(name='asyncio')]),
    Import(
      names=[
        alias(name='re')]),
    ImportFrom(
      module='mcp.server.models',
      names=[
        alias(name='InitializationOptions')],
      level=0),
    Import(
      names=[
        alias(name='mcp.types', asname='types')]),
    ImportFrom(
      module='mcp.server',
      names=[
        alias(name='NotificationOptions'),
        alias(name='Server')],
      level=0),
    Import(
      names=[
        alias(name='mcp.server.stdio')]),
    Assign(
      targets=[
        Name(id='server', ctx=Store())],
      value=Call(
        func=Name(id='Server', ctx=Load()),
        args=[
          Constant(value='pandoras-shell')])),
    AsyncFunctionDef(
      name='handle_list_tools',
      args=arguments(),
      body=[
        Expr(
          value=Constant(value='List available terminal command tools.')),
        Return(
          value=List(
            elts=[
              Call(
                func=Attribute(
                  value=Name(id='types', ctx=Load()),
                  attr='Tool',
                  ctx=Load()),
                keywords=[
                  keyword(
                    arg='name',
                    value=Constant(value='execute_command')),
                  keyword(
                    arg='description',
                    value=Constant(value='Execute SSH command to connect to admin@192.168.0.1')),
                  keyword(
                    arg='inputSchema',
                    value=Dict(
                      keys=[
                        Constant(value='type'),
                        Constant(value='properties'),
                        Constant(value='required')],
                      values=[
                        Constant(value='object'),
                        Dict(
                          keys=[
                            Constant(value='command'),
                            Constant(value='directory')],
                          values=[
                            Dict(
                              keys=[
                                Constant(value='type'),
                                Constant(value='description')],
                              values=[
                                Constant(value='string'),
                                Constant(value='SSH command to execute (must connect to admin@192.168.0.1)')]),
                                Dict(
                              keys=[
                                Constant(value='type'),
                                Constant(value='description'),
                                Constant(value='default')],
                              values=[
                                Constant(value='string'),
                                Constant(value='Working directory (optional)'),
                                Constant(value='~')])]),
                        List(
                          elts=[
                            Constant(value='command')],
                          ctx=Load())]))])],
            ctx=Load()))],
      decorator_list=[
        Call(
          func=Attribute(
            value=Name(id='server', ctx=Load()),
            attr='list_tools',
            ctx=Load()))],
      returns=Subscript(
        value=Name(id='list', ctx=Load()),
        slice=Attribute(
          value=Name(id='types', ctx=Load()),
          attr='Tool',
          ctx=Load()),
        ctx=Load())),
    AsyncFunctionDef(
      name='handle_call_tool',
      args=arguments(
        args=[
          arg(
            arg='name',
            annotation=Name(id='str', ctx=Load())),
          arg(
            arg='arguments',
            annotation=BinOp(
              left=Name(id='dict', ctx=Load()),
              op=BitOr(),
              right=Constant(value=None)))]),
      body=[
        Expr(
          value=Constant(value='Handle tool execution requests.')),
        If(
          test=Compare(
            left=Name(id='name', ctx=Load()),
            ops=[
              NotEq()],
            comparators=[
              Constant(value='execute_command')]),
          body=[
            Raise(
              exc=Call(
                func=Name(id='ValueError', ctx=Load()),
                args=[
                  JoinedStr(
                    values=[
                      Constant(value='Unknown tool: '),
                      FormattedValue(
                        value=Name(id='name', ctx=Load()),
                        conversion=-1)])]))]),
        If(
          test=UnaryOp(
            op=Not(),
            operand=Name(id='arguments', ctx=Load())),
          body=[
            Raise(
              exc=Call(
                func=Name(id='ValueError', ctx=Load()),
                args=[
                  Constant(value='Missing arguments')]))]),
        Assign(
          targets=[
            Name(id='command', ctx=Store())],
          value=Call(
            func=Attribute(
              value=Name(id='arguments', ctx=Load()),
              attr='get',
              ctx=Load()),
            args=[
              Constant(value='command')])),
        Assign(
          targets=[
            Name(id='directory', ctx=Store())],
          value=Call(
            func=Attribute(
              value=Attribute(
                value=Name(id='os', ctx=Load()),
                attr='path',
                ctx=Load()),
              attr='expanduser',
              ctx=Load()),
            args=[
              Call(
                func=Attribute(
                  value=Name(id='arguments', ctx=Load()),
                  attr='get',
                  ctx=Load()),
                args=[
                  Constant(value='directory'),
                  Constant(value='~')])])),
        Assign(
          targets=[
            Name(id='ssh_pattern', ctx=Store())],
          value=Constant(value='^ssh\\s+(?:(?:-\\w+\\s+|\\w+=\\S+\\s+|--\\w+=?\\S*\\s+|-[ilopRD]\\s+\\S+\\s+)*)admin@192\\.168\\.0\\.1\\b')),
        If(
          test=UnaryOp(
            op=Not(),
            operand=Call(
              func=Attribute(
                value=Name(id='re', ctx=Load()),
                attr='match',
                ctx=Load()),
              args=[
                Name(id='ssh_pattern', ctx=Load()),
                Name(id='command', ctx=Load()),
                Attribute(
                  value=Name(id='re', ctx=Load()),
                  attr='IGNORECASE',
                  ctx=Load())])),
          body=[
            Return(
              value=List(
                elts=[
                  Call(
                    func=Attribute(
                      value=Name(id='types', ctx=Load()),
                      attr='TextContent',
                      ctx=Load()),
                    keywords=[
                      keyword(
                        arg='type',
                        value=Constant(value='text')),
                        keyword(
                          arg='text',
                          value=Constant(value='Error: Only SSH commands to admin@192.168.0.1 are allowed.'))
                        ])],
                    ctx=Load()))]),
        Try(
          body=[
            Assign(
              targets=[
                Name(id='result', ctx=Store())],
                value=Call(
                  func=Attribute(
                    value=Name(id='subprocess', ctx=Load()),
                    attr='run',
                    ctx=Load()),
                  args=[
                    Name(id='command', ctx=Load())],
                  keywords=[
                    keyword(
                      arg='shell',
                      value=Constant(value=True)),
                    keyword(
                      arg='cwd',
                      value=Name(id='directory', ctx=Load())),
                    keyword(
                      arg='capture_output',
                      value=Constant(value=True)),
                    keyword(
                      arg='text',
                      value=Constant(value=True)),
                    keyword(
                      arg='timeout',
                      value=Constant(value=300))])),
              Assign(
                targets=[
                  Name(id='output', ctx=Store())],
                  value=JoinedStr(
                    values=[
                      Constant(value='Exit code: '),
                      FormattedValue(
                        value=Attribute(
                          value=Name(id='result', ctx=Load()),
                          attr='returncode',
                          ctx=Load()),
                        conversion=-1),
                      Constant(value='\n\n')])),
              If(
                test=Attribute(
                  value=Name(id='result', ctx=Load()),
                  attr='stdout',
                  ctx=Load()),
                body=[
                  AugAssign(
                    target=Name(id='output', ctx=Store()),
                    op=Add(),
                    value=JoinedStr(
                      values=[
                        Constant(value='STDOUT:\n'),
                        FormattedValue(
                          value=Attribute(
                            value=Name(id='result', ctx=Load()),
                            attr='stdout',
                            ctx=Load()),
                          conversion=-1),
                        Constant(value='\n')]))]),
              If(
                test=Attribute(
                  value=Name(id='result', ctx=Load()),
                  attr='stderr',
                  ctx=Load()),
                body=[
                  AugAssign(
                    target=Name(id='output', ctx=Store()),
                    op=Add(),
                    value=JoinedStr(
                      values=[
                        Constant(value='STDERR:\n'),
                        FormattedValue(
                          value=Attribute(
                            value=Name(id='result', ctx=Load()),
                            attr='stderr',
                            ctx=Load()),
                          conversion=-1),
                        Constant(value='\n')]))]),
              Return(
                value=List(
                  elts=[
                    Call(
                      func=Attribute(
                        value=Name(id='types', ctx=Load()),
                        attr='TextContent',
                        ctx=Load()),
                      keywords=[
                        keyword(
                          arg='type',
                          value=Constant(value='text')),
                          keyword(
                            arg='text',
                            value=Name(id='output', ctx=Load()))])],
                  ctx=Load()))],
            handlers=[
              ExceptHandler(
                type=Attribute(
                  value=Name(id='subprocess', ctx=Load()),
                  attr='TimeoutExpired',
                  ctx=Load()),
                body=[
                  Return(
                    value=List(
                      elts=[
                        Call(
                          func=Attribute(
                            value=Name(id='types', ctx=Load()),
                            attr='TextContent',
                            ctx=Load()),
                          keywords=[
                            keyword(
                              arg='type',
                              value=Constant(value='text')),
                              keyword(
                                arg='text',
                                value=Constant(value='Command timed out after 5 minutes'))])],
                        ctx=Load()))]),
              ExceptHandler(
                type=Name(id='Exception', ctx=Load()),
                name='e',
                body=[
                  Return(
                    value=List(
                      elts=[
                        Call(
                          func=Attribute(
                            value=Name(id='types', ctx=Load()),
                            attr='TextContent',
                            ctx=Load()),
                          keywords=[
                            keyword(
                              arg='type',
                              value=Constant(value='text')),
                              keyword(
                                arg='text',
                                value=JoinedStr(
                                  values=[
                                    Constant(value='Error executing command: '),
                                    FormattedValue(
                                      value=Call(
                                        func=Name(id='str', ctx=Load()),
                                        args=[
                                          Name(id='e', ctx=Load())]),
                                      conversion=-1)]))])],
                        ctx=Load()))])])],
        decorator_list=[
          Call(
            func=Attribute(
              value=Name(id='server', ctx=Load()),
              attr='call_tool',
              ctx=Load()))],
        returns=Subscript(
          value=Name(id='list', ctx=Load()),
          slice=BinOp(
            left=BinOp(
              left=Attribute(
                value=Name(id='types', ctx=Load()),
                attr='TextContent',
                ctx=Load()),
              op=BitOr(),
              right=Attribute(
                value=Name(id='types', ctx=Load()),
                attr='ImageContent',
                ctx=Load())),
            op=BitOr(),
            right=Attribute(
              value=Name(id='types', ctx=Load()),
              attr='EmbeddedResource',
              ctx=Load())),
          ctx=Load())),
    AsyncFunctionDef(
      name='main',
      args=arguments(),
      body=[
        AsyncWith(
          items=[
            withitem(
              context_expr=Call(
                func=Attribute(
                  value=Attribute(
                    value=Attribute(
                      value=Name(id='mcp', ctx=Load()),
                      attr='server',
                      ctx=Load()),
                    attr='stdio',
                    ctx=Load()),
                  attr='stdio_server',
                  ctx=Load())),
              optional_vars=Tuple(
                elts=[
                  Name(id='read_stream', ctx=Store()),
                  Name(id='write_stream', ctx=Store())],
                ctx=Store()))],
          body=[
            Expr(
              value=Await(
                value=Call(
                  func=Attribute(
                    value=Name(id='server', ctx=Load()),
                    attr='run',
                    ctx=Load()),
                  args=[
                    Name(id='read_stream', ctx=Load()),
                    Name(id='write_stream', ctx=Load()),
                    Call(
                      func=Name(id='InitializationOptions', ctx=Load()),
                      keywords=[
                        keyword(
                          arg='server_name',
                          value=Constant(value='pandoras-shell')),
                        keyword(
                          arg='server_version',
                          value=Constant(value='0.1.0')),
                        keyword(
                          arg='capabilities',
                          value=Call(
                            func=Attribute(
                              value=Name(id='server', ctx=Load()),
                              attr='get_capabilities',
                              ctx=Load()),
                            keywords=[
                              keyword(
                                arg='notification_options',
                                value=Call(
                                  func=Name(id='NotificationOptions', ctx=Load()))),
                              keyword(
                                arg='experimental_capabilities', 
                                value=Dict())]))])])))])]),
    If(
      test=Compare(
        left=Name(id='__name__', ctx=Load()),
        ops=[
          Eq()],
        comparators=[
          Constant(value='__main__')]),
      body=[
        Expr(
          value=Call(
            func=Attribute(
              value=Name(id='asyncio', ctx=Load()),
              attr='run',
              ctx=Load()),
            args=[
              Call(
                func=Name(id='main', ctx=Load()))]))])])
```

## Key AST Analysis Points

### Security-Critical Nodes

1. **Command Execution**:
   ```python
   Call(
     func=Attribute(
       value=Name(id='subprocess', ctx=Load()),
       attr='run',
       ctx=Load()),
     args=[
       Name(id='command', ctx=Load())],
     keywords=[
       keyword(
         arg='shell',
         value=Constant(value=True))
       # Other arguments...
     ])
   ```
   The `shell=True` parameter creates a command injection vulnerability.

2. **SSH Pattern Restriction**:
   ```python
   Assign(
     targets=[
       Name(id='ssh_pattern', ctx=Store())],
     value=Constant(value='^ssh\\s+(?:(?:-\\w+\\s+|\\w+=\\S+\\s+|--\\w+=?\\S*\\s+|-[ilopRD]\\s+\\S+\\s+)*)admin@192\\.168\\.0\\.1\\b'))
   ```
   This regex is used to restrict commands to SSH connections to a specific host.

3. **Directory Handling**:
   ```python
   Assign(
     targets=[
       Name(id='directory', ctx=Store())],
     value=Call(
       func=Attribute(
         value=Attribute(
           value=Name(id='os', ctx=Load()),
           attr='path',
           ctx=Load()),
         attr='expanduser',
         ctx=Load()),
       args=[
         Call(
           func=Attribute(
             value=Name(id='arguments', ctx=Load()),
             attr='get',
             ctx=Load()),
           args=[
             Constant(value='directory'),
             Constant(value='~')])]))
   ```
   This expands user directory with no access control.

4. **Exception Handling**:
   ```python
   ExceptHandler(
     type=Name(id='Exception', ctx=Load()),
     name='e',
     body=[...])
   ```
   The broad exception handler could mask security issues.

5. **Timeout Setting**:
   ```python
   keyword(
     arg='timeout',
     value=Constant(value=300))
   ```
   The 5-minute (300 second) timeout may be excessive.

These AST nodes highlight the security concerns identified in the security hardening recommendations document. 