from app.agents.career_agent import career_graph


def main():
    print("=" * 60)
    print("CareerPilot AI - Career Agent")
    print("=" * 60)

    user_message = input("\nYou: ")

    if not user_message.strip():
        print("\nPlease enter a message.")
        return

    try:
        result = career_graph.invoke(
            {
                "user_message": user_message,
                "response": ""
            }
        )

        print("\nCareerPilot AI:")
        print("-" * 60)
        print(result["response"])
        print("-" * 60)

    except Exception as e:
        print("\nError:")
        print(str(e))


if __name__ == "__main__":
    main()