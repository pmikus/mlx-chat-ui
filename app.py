from typing import Dict, Optional

import chainlit as cl
from chainlit.input_widget import Select, Switch, Slider
from openai import AsyncOpenAI

client = AsyncOpenAI(base_url="http://localhost:8080/v1", api_key="fake-key")


@cl.oauth_callback
def oauth_callback(
    provider_id: str,
    token: str,
    raw_user_data: Dict[str, str],
    default_user: cl.User,
) -> Optional[cl.User]:
    return default_user


@cl.on_chat_start
async def start_chat():
    settings = await cl.ChatSettings(
        [
            Select(
                id="model",
                label="LLM - Model",
                values=[
                    "mlx-community/DeepSeek-Coder-V2-Lite-Instruct-4bit-mlx",
                    "mlx-community/DeepSeek-R1-0528-Qwen3-8B-8bit"
                ],
                initial_index=0,
            ),
            Switch(
                id="web_search_options",
                label="Search Web Tool",
                initial=False),
            Slider(
                id="temperature",
                label="Temperature",
                initial=0.7,
                min=0,
                max=2,
                step=0.1,
            ),
        ]
    ).send()

    cl.user_session.set(
        "messages",
        [
            {"role": "system", "content": "You are a helpful assistant."},
            *cl.chat_context.to_openai(),
        ],
    )
    cl.user_session.set("settings", settings)


@cl.on_settings_update
async def setup_agent(settings):
    cl.user_session.set("settings", settings)


@cl.on_message
async def main(message: cl.Message):
    settings = cl.user_session.get("settings")
    messages = cl.user_session.get("messages")

    if settings["web_search_options"]:
        settings["web_search_options"] = {
            "user_location": {
                "type": "approximate",
                "approximate": {
                    "country": "SK",
                    "city": "Bratislava",
                    "region": "Bratislava",
                },
            },
            "search_context_size": "low",
        }

    messages.append({"role": "user", "content": message.content})

    stream = await client.chat.completions.create(
        messages=messages,
        **settings,
        stream=True,
    )

    thinking = False

    # Streaming the thinking
    async with cl.Step(name="Thinking") as thinking_step:
        msg = cl.Message(content="")

        async for chunk in stream:
            delta = chunk.choices[0].delta

            if delta.content == "<think>":
                thinking = True
                continue

            if delta.content == "</think>":
                thinking = False
                await thinking_step.update()
                continue

            if thinking:
                await thinking_step.stream_token(delta.content)
            else:
                await msg.stream_token(delta.content)

    messages.append({"role": "assistant", "content": msg.content})
    await msg.update()
    await msg.send()
