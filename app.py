import chainlit as cl
from chainlit.input_widget import Select, Switch, Slider
from openai import AsyncOpenAI

client = AsyncOpenAI(base_url="http://localhost:8080/v1", api_key="fake-key")


@cl.set_chat_profiles
async def chat_profile():
    return [
        cl.ChatProfile(
            name="DeepSeek-Coder",
            markdown_description="The underlying LLM model is **DeepSeek-Coder-V2-Lite**.",
        ),
    ]


@cl.on_chat_start
async def start_chat():
    settings = await cl.ChatSettings(
        [
            Select(
                id="model",
                label="LLM - Model",
                values=[
                    "mlx-community/DeepSeek-Coder-V2-Lite-Instruct-4bit-mlx"
                ],
                initial_index=0,
            ),
            Switch(
                id="web_search_options",
                label="Search Web Tool",
                initial=False
            ),
            Slider(
                id="temperature",
                label="Temperature",
                initial=0.7,
                min=0,
                max=2,
                step=0.1,
            ),
            Slider(
                id="top_p",
                label="Top P",
                initial=0.7,
                min=0,
                max=1,
                step=0.1,
            ),
            Slider(
                id="max_output_tokens",
                label="Max output tokens",
                initial=512,
                min=0,
                max=1024,
                step=64,
            ),
        ]
    ).send()

    cl.user_session.set(
        "messages",
        [{"role": "system", "content": "You are a helpful assistant."}],
    )
    cl.user_session.set("settings", settings)


@cl.on_settings_update
async def setup_agent(settings):
    cl.user_session.set("settings", settings)


@cl.on_message
async def main(message: cl.Message):
    settings = cl.user_session.get("settings")
    messages = cl.user_session.get("messages")
    messages.append({"role": "user", "content": message.content})

    msg = cl.Message(content="")
    await msg.send()

    stream = await client.chat.completions.create(
        messages=messages, **settings, stream=True,
    )

    async for part in stream:
        if token := part.choices[0].delta.content or "":
            await msg.stream_token(token)

    messages.append({"role": "assistant", "content": msg.content})
    await msg.update()