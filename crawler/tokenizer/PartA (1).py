import sys


def tokenize(file_path):
    """ Runtime Complexity: O(n)
    This method reads the input file 1 char at a time, identifying sequences of ASCII (English)
    alphanumeric characters as valid tokens (words). Non-alphanumeric or non-English characters act
    as delimiters that mark the end of a token. Since each character in the file is processed
    exactly once using constant-time operations, the overall runtime complexity grows linearly
    with the size of the file, resulting in O(n), where n is the number of characters in the file."""
    token_list = []
    token = ""
    try:
        with open(file_path, 'r', encoding = 'utf-8', errors = 'ignore') as file:
            while True:
                char = file.read(1)
                if not char:
                    break
                if char.isascii() and char.isalnum():
                    token += char
                else:
                    if token:
                        token_list.append(token.lower())
                        token = ""
            if token:
                token_list.append(token.lower())
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        sys.exit(1)
    except Exception as error:
        print(f"Error while reading file:\n{error}")
        sys.exit(1)
    return token_list


def computeWordFrequencies(token_list):
    #TODO: make sure english based (no chinese or other chars treat as delimeters)
    """ Runtime Complexity: O(m)
    This method takes the list of tokens produced by the tokenizer and counts how often each one
    appears by iterating once through the token list and using a dictionary to generate frequency
    counts. Each dictionary insertion or update operation runs in constant average time, meaning
    the total runtime scales linearly with the number of tokens processed, meaning its runtime
    complexity is O(m), where m is the total number of tokens."""
    token_freq = {}
    for token in token_list:
        if token in token_freq:
            token_freq[token] +=1
        else:
            token_freq[token] = 1
    return token_freq

def printFrequencies(token_freq):
    """ Runtime Complexity: O(k log k)
    This method sorts and displays the token frequencies in descending order. While printing itself
    takes linear time, sorting the tokens by frequency dominates the runtime. Python’s built-in
    sorted() function uses Timsort, which has an average and worst-case complexity of O(k log k),
    where k is the number of unique tokens. Therefore, the overall runtime complexity for this
    method is O(k log k)."""
    sorted_tokens = sorted(token_freq.items(), key = lambda x: x[1], reverse=True)
    for token, count in sorted_tokens:
        print(f"{token} = {count}")


if __name__ == "__main__":
    """Runtime Complexity: O(n + m + k log k)
    The main section of Part A orchestrates the tokenization, frequency computation, and frequency 
    printing processes. It first processes the file (O(n)), then computes word frequencies (O(m)), 
    and then sorts and prints them (O(k log k)). The overall runtime is O(n + m + k log k), where n 
    (the number of characters) is typically much larger than m or k, the tokenization and sorting 
    steps dominate the runtime."""
    if len(sys.argv) != 2:
        print("Incorrect input format (python3 PartA.py <textfile>)")
        sys.exit(1)

    file_path = sys.argv[1]
    token_list = tokenize(file_path)
    token_freq = computeWordFrequencies(token_list)
    printFrequencies(token_freq)
