import asyncio
import json
import os
from contextlib import AsyncExitStack
from typing import Optional

from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from openai import OpenAI

load_dotenv()


class MCPClient:
    def __init__(self):
        self.write = None
        self.stdio = None
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    async def connect_to_server(self, server_script_path: str):
        """Connect to an MCP server

        Args:
            server_script_path: Path to the server script (.py or .js)
        """
        is_python = server_script_path.endswith('.py')
        is_js = server_script_path.endswith('.js')
        if not (is_python or is_js):
            raise ValueError("Server script must be a .py or .js file")

        command = "python" if is_python else "node"
        server_params = StdioServerParameters(
            command=command,
            args=[server_script_path],
            env=None
        )

        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
        self.stdio, self.write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))

        await self.session.initialize()

        response = await self.session.list_tools()
        tools = response.tools
        print("\nConnected to server with tools:", [tool.name for tool in tools])

    async def process_query(self, query: str) -> str:
        """Process a query using the LLM and available MCP tools."""
        messages = [
            {"role": "user", "content": query}
        ]

        # 1) Fetch available tools from the MCP server and build OpenAI 'functions' spec
        response = await self.session.list_tools()
        available_functions = []
        for tool in response.tools:
            available_functions.append({
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.inputSchema
            })

        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=1000,
            functions=available_functions,
            function_call="auto"
        )

        msg = response.choices[0].message

        # 2) If the model returned plain text, just return it
        if msg.content:
            return msg.content

        # 3) Otherwise it requested a function call
        if not msg.function_call:
            return ""

        fn_name = msg.function_call.name
        raw_args = msg.function_call.arguments
        try:
            fn_args = json.loads(raw_args)
        except json.JSONDecodeError:
            raise RuntimeError(f"Could not parse function_call.arguments: {raw_args!r}")

        print(f"\nCalling function: {fn_name} with args: {fn_args}")
        tool_result = await self.session.call_tool(fn_name, fn_args)

        # 4) Inject the function call and its result back into the conversation
        messages.append({
            "role": "assistant",
            "content": None,
            "function_call": {
                "name": fn_name,
                "arguments": raw_args
            }
        })
        messages.append({
            "role": "function",
            "name": fn_name,
            "content": tool_result.content
        })

        final_resp = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=150
        )

        return f"Answer: {final_resp.choices[0].message.content}"

    async def chat_loop(self):
        """Run an interactive chat loop"""
        print("\nMCP Client Started!")
        print("Type your queries or 'quit' to exit.")

        while True:
            try:
                query = input("\nQuery: ").strip()

                if query.lower() == 'quit':
                    break

                response = await self.process_query(query)
                print("\n" + response)

            except Exception as e:
                print(f"\nError: {str(e)}")

    async def cleanup(self):
        """Clean up resources"""
        await self.exit_stack.aclose()


async def main():
    if len(sys.argv) < 2:
        print("Usage: python client.py <path_to_server_script>")
        sys.exit(1)

    client = MCPClient()
    try:
        await client.connect_to_server(sys.argv[1])
        await client.chat_loop()
    finally:
        await client.cleanup()


if __name__ == "__main__":
    import sys

    asyncio.run(main())
