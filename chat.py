import ollama

def chat_with_mistral(temperature=0.8, top_p=0.7):
    while True:
        try:
            question = input("Enter your question (or 'exit' to quit): ")
            if question.lower() == "exit":
                break
            
            messages = [
                {'role': 'system', 'content': 'Responses should be short and clear.'},
                {'role': 'user', 'content': question}
            ]
            
            # Настройка параметров генерации
            stream = False  # Disable streaming
            result = ollama.chat(
                model='mistral',  # Используем модель Mistral
                messages=messages,
                stream=stream,
                options={
                    "temperature": temperature,
                    "top_p": top_p,
                    "stop": ["<|im_start|>", "<|im_end|>"]
                }
            )
            print(result['message']['content'])
        except Exception as e:
            print(f"An error occurred: {e}")

# Запуск чата с настройками по умолчанию
chat_with_mistral()
