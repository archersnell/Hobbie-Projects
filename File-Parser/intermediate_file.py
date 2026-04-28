import basic_file
import re

def word_count():
    words = get_words()
    print(len(words))


def get_words():
    file_name = input("Enter the name of the file you want to count: ")
    text = basic_file.read_file(file_name)
    if text == "File not found.":
        return []
    

    DELIMITERS = [",", ";", "|"]
    pattern = r"[\s" + re.escape("".join(DELIMITERS)) + r"]+"
    words = re.split(pattern, text.strip())


    return words

