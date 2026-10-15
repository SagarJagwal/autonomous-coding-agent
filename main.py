
from agent.graph import run_agent


def main():
    task = input("Describe the Python task: ").strip()

    if not task:
        print("Please enter a task.")
        return

    result = run_agent(task)

    print("\n--- Agent Result ---")
    print("Success:", result["success"])
    print("Attempts:", result["attempts"])
    print("\nOutput:")
    print(result["output"])

    if result["error"]:
        print("\nErrors:")
        print(result["error"])


if __name__ == "__main__":
    main()
