import chainlit as cl
from chainlit.input_widget import Select, Switch, Slider
from openai import AsyncOpenAI

client = AsyncOpenAI(base_url="http://localhost:8080/v1", api_key="fake-key")


@cl.set_chat_profiles
async def chat_profile():
    return [
        cl.ChatProfile(
            name="Personal",
            markdown_description="Personal chat space.",
        ),
        cl.ChatProfile(
            name="Workspace 1",
            markdown_description="Coding workspace 1.",
        ),
    ]


@cl.on_chat_start
async def start_chat():
    chat_profile = cl.user_session.get("chat_profile")
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

#    async for part in stream:
#        if token := part.choices[0].delta.content or "":
#            await msg.stream_token(token)

    thinking = False

    # Streaming the thinking
    async with cl.Step(name="Thinking") as thinking_step:
        final_answer = cl.Message(content="")

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
                await final_answer.stream_token(delta.content)

    messages.append({"role": "assistant", "content": msg.content})
    await msg.update()