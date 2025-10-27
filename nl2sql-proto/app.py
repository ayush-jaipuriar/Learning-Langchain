import argparse
import json

from agent_chain import run_nl_to_sql


def main() -> None:
    parser = argparse.ArgumentParser(description="Natural language to SQL prototype")
    parser.add_argument("--q", required=True, help="Natural language query")
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format",
    )
    args = parser.parse_args()

    result = run_nl_to_sql(args.q)

    if args.format == "json":
        print(json.dumps(result, indent=2))
        return

    print("\n=== Generated SQL ===\n")
    print(result["sql"])
    print("\n=== Verifier ===\n")
    print(json.dumps(result["verifier"], indent=2))
    print("\n=== IR ===\n")
    print(json.dumps(result["ir"], indent=2))


if __name__ == "__main__":
    main()

