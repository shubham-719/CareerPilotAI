from app.agents.job_agent import job_graph


def main():
    print("=" * 60)
    print("CareerPilot AI - Job Agent Test")
    print("=" * 60)

    user_message = input(
        "\nEnter your job-related request: "
    )

    if not user_message.strip():
        print("\nPlease enter a request.")
        return

    try:
        result = job_graph.invoke(
            {
                "user_message": user_message,
                "response": ""
            }
        )

        print("\nJob Agent:")
        print("-" * 60)
        print(result["response"])
        print("-" * 60)

    except Exception as e:
        print("\nError:")
        print(str(e))


if __name__ == "__main__":
    main()