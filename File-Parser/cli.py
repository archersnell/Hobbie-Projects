import basic_file
import intermediate_file


def func_helper(func):
    if func in {"help", "-h"}:
        print("Commands:\n-read --r\n-create --c\n-delete --d\n-count --cnt\nexit")
    elif func in {"-read", "--r"}:
        print(basic_file.read_file())
    elif func in {"-create", "--c"}:
        basic_file.create_file()
    elif func in {"-delete", "--d"}:
        basic_file.delete_file()
    elif func in {"-count", "--cnt"}:
        intermediate_file.word_count()
    else:
        print("Unknown command. Type 'help' to see the options.")

