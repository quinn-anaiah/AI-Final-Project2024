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
        # Degree Heuristic: Find the cell involved in the most constraints (row, col, block)
        max_constraints = -1
        best_cell = None
        for row in range(9):
            for col in range(9):
                if board[row][col] == 0:  # Find empty cells
                    constraints = 0
                    # Count constraints in the row
                    constraints += sum(1 for i in range(9) if board[row][i] != 0)
                    # Count constraints in the column
                    constraints += sum(1 for i in range(9) if board[i][col] != 0)
                    # Count constraints in the 3x3 subgrid
                    start_row, start_col = 3 * (row // 3), 3 * (col // 3)
                    constraints += sum(1 for i in range(3) for j in range(3) 
                                       if board[start_row + i][start_col + j] != 0)
                    if constraints > max_constraints:
                        max_constraints = constraints
                        best_cell = (row, col)
        return best_cell
    else:
        # If no heuristic, just pick the first empty location
        for row in range(9):
            for col in range(9):
                if board[row][col] == 0:
                    return (row, col)
    return None

# Implementing the AC-3 algorithm for Arc Consistency
def ac3(board):
    # Set up the domains for each cell: 1-9 for each empty cell, else the fixed number
    domains = {}
    for row in range(9):
        for col in range(9):
            if board[row][col] == 0:  # Empty cell, initial domain is 1-9
                domains[(row, col)] = set(range(1, 10))
            else:  # Fixed number, domain is just that number (in a set)
                domains[(row, col)] = {board[row][col]}

    # Queue of arcs (variables to check)
    queue = deque()

    # Add all arcs (row, col) with their neighboring constraints (row, col)
    for row in range(9):
        for col in range(9):
            if board[row][col] == 0:
                neighbors = get_neighbors(row, col)
                for neighbor in neighbors:
                    queue.append(((row, col), neighbor))

    # AC-3 algorithm
    while queue:
        (x, y), (i, j) = queue.popleft()
        
        if revise(domains, x, y):
            if len(domains[(x, y)]) == 0:
                return False  # Failure, no solution
            neighbors = get_neighbors(x, y)
            for neighbor in neighbors:
                if neighbor != (i, j):
                    queue.append(((x, y), neighbor))

    return True  # AC-3 succeeded

def revise(domains, x, y):
    revised = False
    # For each value in the domain of x, check if it has a consistent value in the domain of y
    for value_x in list(domains[(x[0], x[1])]):
        if not any(value_x != value_y for value_y in domains[(y[0], y[1])]):
            domains[(x[0], x[1])].remove(value_x)
            revised = True
    return revised

def get_neighbors(row, col):
    """Get all neighboring cells of (row, col) that aren't the same cell."""
    neighbors = []
    for i in range(9):
        if i != row:
            neighbors.append((i, col))  # Row neighbors
        if i != col:
            neighbors.append((row, i))  # Column neighbors
    # Subgrid neighbors
    start_row, start_col = 3 * (row // 3), 3 * (col // 3)
    for i in range(start_row, start_row + 3):
        for j in range(start_col, start_col + 3):
            if (i, j) != (row, col):
                neighbors.append((i, j))
    return neighbors

def solve_sudoku(board, method="backtracking", heuristic=None):
    # Choose solving method based on the user input
    if method == "arc":
        print("\nApplying Arc Consistency (AC-3)...")
        if not ac3(board):
            print("No solution found after applying AC-3.")
            return False
        print("Arc Consistency applied successfully.\n")

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

    # Ask the user for the solving method: backtracking or arc consistency (AC-3)
    print("\nChoose the solving method:")
    print("1: Backtracking")
    print("2: Arc Consistency (AC-3)")
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
    heuristic_choice = input("Enter 1 or 2: ").strip()

    if heuristic_choice == "1":
        heuristic = "none"
    elif heuristic_choice == "2":
        heuristic = "Degree"
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
