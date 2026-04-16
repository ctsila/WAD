from app.services.llm_service import generate_response


if __name__ == "__main__":
    prompt = "User: Hello\nAssistant:"
    print(generate_response(prompt))
