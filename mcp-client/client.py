import asyncio
import json
from contextlib import AsyncExitStack
from typing import Optional, Union, Mapping, Any, List

from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from ollama import Client, ChatResponse, Message

load_dotenv()


class MCPClient:
    def __init__(self):
        self.write = None
        self.stdio = None
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.ollama_client = Client("http://localhost:11434")

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
        messages: List[Union[Mapping[str, Any], Message]] = [
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

        response: ChatResponse = self.ollama_client.chat(
            model="llama3.2:3b",
            messages=messages,
            tools=available_functions
        )

        msg: Message = response.message

        # 2) If the model returned plain text, just return it
        if msg.content:
            return msg.content

        # 3) Otherwise it requested a function call
        if msg.tool_calls.count == 0:
            return ""

        tool_call = msg.tool_calls[0]
        fn_name = tool_call.function.name
        raw_args = tool_call.function.arguments

        if isinstance(raw_args, str):
            try:
                fn_args = json.loads(raw_args)
            except json.JSONDecodeError:
                raise RuntimeError(f"Could not parse function_call.arguments: {raw_args!r}")
        elif isinstance(raw_args, dict):
            fn_args = raw_args
        else:
            raise RuntimeError(f"Unexpected type for function_call.arguments: {type(raw_args)}")

        print(f"\nCalling function: {fn_name} with args: {fn_args}")
        tool_result = await self.session.call_tool(fn_name, fn_args)

        print("Function result:", tool_result.content)
        # 4) Inject the function call and its result back into the conversation
        if isinstance(tool_result.content, list):
            func_output = "\n\n".join(tc.text for tc in tool_result.content)
        else:
            # fallback: if it's already a str
            func_output = str(tool_result.content)
        messages.append({
            "role": "assistant",
            "function_call": {
                "name": fn_name,
                "arguments": json.dumps(fn_args)
            }
        })

        # 5) Inject the function’s response as a proper function-message:
        messages.append({
            "role": "function",
            "name": fn_name,
            "content": func_output  # THIS is a plain string
        })

        final_resp: ChatResponse = self.ollama_client.chat(
            model="llama3.2:3b",
            messages=messages,
        )

        return f"Answer: {final_resp.message.content}"

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
