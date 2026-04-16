import asyncio

from app.services.llm_service import stream_response


async def main():
    prompt = "User: Hello\nAssistant:"
    async for token in stream_response(prompt):
        print(token, end="", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
