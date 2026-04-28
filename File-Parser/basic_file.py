import os


def read_file(file_name=None):
    if file_name is None:
        file_name = input("Enter the name of the file you want to read: ")
    try:
        with open(file_name, "r") as f:
            return f.read()
    except FileNotFoundError:
        return "File not found."


def create_file(file_name=None):
    if file_name is None:
        file_name = input("Enter the name of the file you want to create: ")
    if not file_name.endswith(".txt"):
        file_name += ".txt"
    with open(file_name, "w") as f:
        content = input("What do you want to write?\n")
        f.write(content)
    print(file_name + " was created")


def delete_file(file_name=None):
    if file_name is None:
        file_name = input("Enter the name of the file you want to delete: ")
    if os.path.exists(file_name):
        os.remove(file_name)
        print(file_name + " was deleted")
    else:
        print("File not found")
