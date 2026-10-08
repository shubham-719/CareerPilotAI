from app.agents.router_agent import router_graph


def main():
    print("=" * 60)
    print("CareerPilot AI - Router Agent Test")
    print("=" * 60)

    test_messages = [
        "Please improve my resume for a software developer job.",
        "Find Python developer jobs for me.",
        "Give me 20 Python interview questions.",
        "I want to become a full stack developer.",
        "What is Python?"
    ]

    for message in test_messages:
        print("\nUser:")
        print(message)

        try:
            result = router_graph.invoke(
                {
                    "user_message": message,
                    "intent": ""
                }
            )

            print("Detected Intent:")
            print(result["intent"])

        except Exception as e:
            print("Error:")
            print(str(e))


if __name__ == "__main__":
    main()