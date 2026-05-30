import asyncio
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage

async def main():
    llm = ChatOllama(model="gemma4:31b", temperature=0.2, num_predict=200)

    # Test 1: simple string invoke
    resp = await llm.ainvoke("Say only the word: HELLO")
    print("Test1 type:", type(resp).__name__)
    print("Test1 content:", repr(resp.content[:200]))

    # Test 2: JSON output
    resp2 = await llm.ainvoke([
        SystemMessage(content="You are a JSON API. Output only valid JSON."),
        HumanMessage(content='Output: {"category": "Account", "priority": "High", "confidence": 8, "grounded": true, "reply": "Please reset your password."}'),
    ])
    print("Test2:", repr(resp2.content[:300]))

asyncio.run(main())
