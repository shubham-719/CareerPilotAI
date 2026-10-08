from app.agents.interview_agent import interview_graph


def main():
    print("=" * 60)
    print("CareerPilot AI - Interview Agent Test")
    print("=" * 60)

    user_message = input(
        "\nEnter your interview-related request: "
    )

    if not user_message.strip():
        print("\nPlease enter a request.")
        return

    try:
        result = interview_graph.invoke(
            {
                "user_message": user_message,
                "response": ""
            }
        )

        print("\nInterview Agent:")
        print("-" * 60)
        print(result["response"])
        print("-" * 60)

    except Exception as e:
        print("\nError:")
        print(str(e))


if __name__ == "__main__":
    main()