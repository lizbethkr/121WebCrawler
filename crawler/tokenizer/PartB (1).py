import sys
from PartA import tokenize

def findCommonTokens(file1, file2):
    """Runtime complexity: O(n1+n2)
    It takes O(n) to tokenize a file, meaning that tokenizing the 2 input files costs O(n1+n2) for
    input file1 and file2. Converting each token list into a set involves inserting each token into
    a hash set which costs O(m1+m2) since insertion is in done in constant time (since it's hash
    based). Finally, the intersection is done in O(min(k1,k2)) since each look up is done in
    constant time based on the smaller set. The overall time complexity O(n1+n2)+O(m1+m2)+O(min(k1,k2))
    which is dominated by O(n1+n2) since n >= k and m."""
    token_list1 = set(tokenize(file1))
    token_list2 = set(tokenize(file2))

    common_tokens = token_list1.intersection(token_list2)
    # print(common_tokens)
    return len(common_tokens)

if __name__ == "__main__":
    """Runtime complexity: O(n1+n2)
     Since the main work is done inside findCommonTokens(), the overall runtime of this method 
     remains O(n1+n2), dominated by the cost of tokenizing both input files."""

    if len(sys.argv) != 3:
        print("Incorrect input format (python3 PartB.py <file1> <file2>)")
        sys.exit(1)

    file1, file2 = sys.argv[1], sys.argv[2]
    count = findCommonTokens(file1, file2)
    print(count)
