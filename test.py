import openai
import os

openai.api_key = "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"
openai.organization = "org-qHlMuocPafW8eM2lczMDUx2C"


model_name = "gpt-3.5-turbo-0613"

question = "pyenvとpipenvの環境構築方法について教えてください。"

response = openai.ChatCompletion.create(
    model=model_name,
    messages=[
        {"role": "user", "content": question},
    ],
)
print(response.choices[0]["message"]["content"].strip())