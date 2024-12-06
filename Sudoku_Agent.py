import csv
import sys
import time
from collections import deque

def read_sudoku_from_csv(filename):
    board = []
    try:
        with open(filename, 'r', encoding='utf-8-sig') as file:
            reader = csv.reader(file)
            for row in reader:
                if len(row) != 9:
                    raise ValueError(f"Each row must contain 9 cells, found row with {len(row)} cells.")
                board.append([int(cell) for cell in row])
            print('Initial Board:')
            print_board(board)
        return board
    except FileNotFoundError:
        print(f"Error: The file {filename} was not found.")
        sys.exit(1)
    except ValueError as e:
        print(f"Error reading the CSV file: {e}")
        sys.exit(1)

def print_board(board):
    """Print the Sudoku board with individual boxes around each number, separated by lines."""
    for i, row in enumerate(board):
        if i % 3 == 0 and i != 0:
            print("+---+---+---+---+---+---+---+---+---+")

        for j, cell in enumerate(row):
            if j % 3 == 0 and j != 0:
                print(" |", end=" ")

            print(f" {cell if cell != 0 else '.'} ", end=" ")

        print()
    print("+---+---+---+---+---+---+---+---+---+")

def is_safe(board, row, col, num):
    # Check the row and column
    for i in range(9):
        if board[row][i] == num or board[i][col] == num:
            return False

    # Check the 3x3 subgrid
    start_row, start_col = 3 * (row // 3), 3 * (col // 3)
    for i in range(3):
        for j in range(3):
            if board[start_row + i][start_col + j] == num:
                return False
    return True

def find_empty_location(board, heuristic=None):
    if heuristic == "Degree":
        return degree_heuristic(board)
    elif heuristic == "MRV":
        return mrv_heuristic(board)
    else:
        # If no heuristic, pick the first empty location
        for row in range(9):
            for col in range(9):
                if board[row][col] == 0:
                    return (row, col)
    return None

def mrv_heuristic(board):
    min_domain_size = float('inf')
    selected_var = None
    for row in range(9):
        for col in range(9):
            if board[row][col] == 0:  # Unassigned variable
                domain_size = len(get_domain(board, row, col))
                if domain_size < min_domain_size:
                    min_domain_size = domain_size
                    selected_var = (row, col)
    return selected_var

def degree_heuristic(board):
    max_degree = -1
    selected_var = None
    for row in range(9):
        for col in range(9):
            if board[row][col] == 0:  # Unassigned variable
                degree = count_constraints(board, row, col)
                if degree > max_degree:
                    max_degree = degree
                    selected_var = (row, col)
    return selected_var

def count_constraints(board, row, col):
    degree = 0
    # Check row
    for i in range(9):
        if board[row][i] != 0:
            degree += 1
    # Check column
    for i in range(9):
        if board[i][col] != 0:
            degree += 1
    # Check block
    block_row, block_col = (row // 3) * 3, (col // 3) * 3
    for i in range(3):
        for j in range(3):
            if board[block_row + i][block_col + j] != 0:
                degree += 1
    return degree

def get_domain(board, row, col):
    domain = set(range(1, 10))
    for i in range(9):
        domain.discard(board[row][i])  # Row constraint
        domain.discard(board[i][col])  # Column constraint

    # Block constraint
    start_row, start_col = 3 * (row // 3), 3 * (col // 3)
    for i in range(3):
        for j in range(3):
            domain.discard(board[start_row + i][start_col + j])

    return domain

def ac(board):
    queue = []
    rows, cols = len(board), len(board[0])

    # Create initial domains from the board
    domains = {}
    for r in range(rows):
        for c in range(cols):
            if board[r][c] == 0:
                domains[(r, c)] = set(range(1, 10))  # Initialize domains with 1-9 for empty cells
            else:
                domains[(r, c)] = {board[r][c]}  # Set domain to the single value for filled cells

    for r in range(rows):
        for c in range(cols):
            if board[r][c] == 0:
                neighbors = get_neighbors(r, c, rows, cols)
                for neighbor in neighbors:
                    queue.append(((r, c), neighbor))

    while queue:
        (xi, yi) = queue.pop(0)
        if revise(domains, xi, yi):
            if len(domains[xi]) == 0:  # Domain is empty
                return False
            # Add neighboring arcs of xi to the queue
            neighbors = get_neighbors(xi[0], xi[1], rows, cols)
            for neighbor in neighbors:
                if neighbor != yi:
                    queue.append((neighbor, xi))

    return True

def revise(domains, xi, yi):
    revised = False
    for x in list(domains[xi]):
        if not any(is_consistent(x, y) for y in domains[yi]):
            domains[xi].remove(x)  # Remove inconsistent value
            revised = True
    return revised

def is_consistent(x, y):
    # Consistency check: Values x and y are consistent if they are not equal
    return x != y

def get_neighbors(r, c, rows, cols):
    # Get neighbors for a given cell (r, c)
    neighbors = set()

    # Row and column constraints
    for i in range(cols):
        if i != c:
            neighbors.add((r, i))
    for i in range(rows):
        if i != r:
            neighbors.add((i, c))

    # 3x3 block constraints
    block_r = r // 3 * 3
    block_c = c // 3 * 3
    for i in range(block_r, block_r + 3):
        for j in range(block_c, block_c + 3):
            if (i, j) != (r, c):
                neighbors.add((i, j))  # Same 3x3 block

    return neighbors

def solve_sudoku(board, method="backtracking", heuristic=None):
    # Choose solving method based on the user input
    if method == "arc":
        if not ac(board):
            print("No solution found after applying AC.")
            return False

    empty = find_empty_location(board, heuristic)
    if not empty:
        return True  # Solved
    row, col = empty

    # Try numbers 1-9
    for num in range(1, 10):
        if is_safe(board, row, col, num):
            board[row][col] = num
            if solve_sudoku(board, method, heuristic):
                return True
            board[row][col] = 0  # Backtrack

    return False  # Trigger backtracking

def main():
    if len(sys.argv) != 2:
        print("Usage: python sudoku_solver.py <csv_file_path>")
        sys.exit(1)
    
    board = read_sudoku_from_csv(sys.argv[1])

    # Ask the user for the solving method: backtracking or arc consistency (AC)
    print("\nChoose the solving method:")
    print("1: Backtracking")
    print("2: Arc Consistency")
    choice = input("Enter 1 or 2: ").strip()

    if choice == "1":
        method = "backtracking"
    elif choice == "2":
        method = "arc"
    else:
        print("Invalid choice. Defaulting to backtracking.")
        method = "backtracking"

    # Ask for the heuristic option
    print("\nChoose the heuristic:")
    print("1: No heuristic")
    print("2: Degree heuristic")
    print("3: MRV heuristic")
    heuristic_choice = input("Enter 1, 2, or 3: ").strip()

    if heuristic_choice == "1":
        heuristic = "none"
    elif heuristic_choice == "2":
        heuristic = "Degree"
    elif heuristic_choice == "3":
        heuristic = "MRV"
    else:
        print("Invalid choice. Defaulting to no heuristic.")
        heuristic = "none"

    start_time = time.time()  # Start the timer
    print("Solving the Sudoku puzzle...\n")
    
    if solve_sudoku(board, method, heuristic):
        print("Sudoku solved successfully:")
        print_board(board)
    else:
        print("No solution exists for the Sudoku puzzle.")
    
    end_time = time.time()  # End the timer
    print(f"Time taken to solve the puzzle: {end_time - start_time:.4f} seconds.")

if __name__ == "__main__":
    main()
