from app.agents.master_graph import master_graph


def main():
    print("=" * 60)
    print("CareerPilot AI - Master Multi-Agent Test")
    print("=" * 60)

    test_messages = [
        "Improve my resume summary for a Python developer job.",
        "What software development jobs should I apply for?",
        "Give me 5 Python interview questions.",
        "Give me a roadmap to become a full stack developer."
    ]

    for message in test_messages:
        print("\nUser:")
        print(message)

        try:
            result = master_graph.invoke(
                {
                    "user_message": message,
                    "intent": "",
                    "response": ""
                }
            )

            print("\nDetected Intent:")
            print(result["intent"])

            print("\nAgent Response:")
            print("-" * 60)
            print(result["response"])
            print("-" * 60)

        except Exception as e:
            print("\nError:")
            print(str(e))


if __name__ == "__main__":
    main()