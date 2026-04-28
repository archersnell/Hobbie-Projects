import basic_file
import intermediate_file
import cli


def main():
    while True:
        func = input("Hello! How can I help you? ").strip().lower()
        if func == "exit":
            print("Goodbye!")
            break
        cli.func_helper(func)


if __name__ == "__main__":
    main()
