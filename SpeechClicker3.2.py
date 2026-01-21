import os
import random
import sys
import subprocess

# --- Check and Install pandas (if needed) ---
try:
    import pandas as pd
except ImportError:
    print("Package 'pandas' not found. Attempting to install...")
    try:
        # Use subprocess to call pip and install pandas
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pandas'])
        print("'pandas' installed successfully.")
        # Try importing again after installation
        import pandas as pd
    except subprocess.CalledProcessError as e:
        print(f"Error: Failed to install 'pandas'. Please install it manually.")
        print(f"The command 'pip install pandas' failed with error: {e}")
        # Exit the program if a critical dependency can't be installed
        sys.exit(1)
    except ImportError:
        # Should not happen if installation was successful, but as a fallback
        print("Error: 'pandas' failed to import even after attempted installation.")
        sys.exit(1)

# --- Standard Library Imports (Should always work) ---
import tkinter as tk
from tkinter import filedialog

# All required tools are now loaded: tk, filedialog, pd, os, random
print("All required packages are loaded and ready.")
# You can now proceed with the rest of your program


##############################################################################################################################################################################

# COMMENCE PROGRAM

def clear_screen():
    # For Windows
    if os.name == "nt":
        os.system("cls")
    # For macOS/Linux
    else:
        os.system("clear")


# Welcome message
print("Welcome to SpeechClicker! Press Enter to Start.\n")
input()


# Open a file dialog to select a csv file
root = tk.Tk()
root.withdraw()  # Hide the root window
file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])

#file_path = input("Please enter the path to the CSV file: ")

try:
    df = pd.read_csv(file_path)
    print("✅ File loaded successfully!\n")
except FileNotFoundError:
    print("❌ The file was not found. Please check the path and try again.")
    exit()
except Exception as e:
    print(f"❌ An error occurred while opening the file: {e}")
    print("Please check the file format and try again.")

# Step 2: Show available columns
print("Available columns:")
print(df.columns.tolist())

# Step 3: Ask for column name repeatedly until a valid one is entered
while True:
    column_name = input("\nWhich column do you want to investigate? ")

    # Check if the column name exists in the DataFrame's columns
    if column_name in df.columns:
        # If valid, break the loop and continue with the rest of the program
        print(f"✅ Column '{column_name}' selected for investigation.")
        break
    else:
        # If invalid, print an error and the loop will restart
        print(f"❌ Column '{column_name}' does not exist in this file.")
        print("Please check the column name and try again.")
        # The loop simply restarts, prompting the user again



# Let the user choose between "browsing mode" and "annotation mode"
while True:
    mode = input("\nChoose mode: \n"
             "'browse' to explore data and leave notes, \n"  
             "'annotate' to assign labels for future ML applications. ")
    
    if mode in ['browse', 'annotate']:
        break

    else:
        print("❌ Invalid mode selected.")

# --- Annotation Mode Implementation ---
if mode == 'annotate':
    clear_screen()
    print("--- Annotation Mode Selected ---")
    
    # 1. Get user-defined labels
    labels_input = input("Enter labels separated by a comma (e.g., 'positive,negative,neutral'): ")
    labels = [label.strip() for label in labels_input.split(',') if label.strip()]
    
    if not labels:
        print("❌ No valid labels entered. The program will exit.")
        exit()

    # Create key-to-label map and instructions
    label_map = {str(i + 1): label for i, label in enumerate(labels)}
    annotation_instructions = [
        f"  - Press '{key}' for '{label}'" for key, label in label_map.items()
    ]
    
    # Ensure "user_label" column exists
    if "user_label" not in df.columns:
        df["user_label"] = ""
    
    # Prepare a list of indices to iterate through (randomized)
    available_indices = list(range(len(df)))
    random.shuffle(available_indices)
    
    current_index_pos = 0 # Position in the available_indices list

    print("\nStarting annotation...")
    
    while current_index_pos < len(available_indices):
        
        # Get the actual index in the DataFrame from the shuffled list
        df_index = available_indices[current_index_pos] 
        
        clear_screen()
        
        print("--- Annotation Mode ---")
        print(f"[{current_index_pos+1}/{len(available_indices)}] Current Entry:")
        print(f"  > {df[column_name].iloc[df_index]}")
        
        # Show existing annotation if any
        current_annotation = df["user_label"].iloc[df_index]
        if current_annotation:
            print(f"🏷️ Existing annotation: {current_annotation}")
            
        print("\nAnnotation Options:")
        print('\n'.join(annotation_instructions))
        
        user_input = input(
            "\n"
            "Input a number to annotate, **press Enter to skip**, type 'back' for previous, "
            "type 'exit' to save and quit, or 'new' to load a new file.\n"
        ).lower()
        
        # --- Handle User Input ---
        
        if user_input.lower() == "exit":
                    # Determine the default 'edited' file path
                    edited_path = file_path.replace(".csv", "_edited.csv")
                    
                    print(f"\n\nYou are about to save your annotations.")
                    print(f"Option 1: Overwrite original file (by typing 'yes').")
                    print(f"Option 2: Save as new file (e.g., '{edited_path}').")

                    confirm = input("\nType 'yes' to overwrite, or enter a new file name: ")
                    
                    if confirm.lower() == "yes":
                        # User chose to OVERWRITE the original file
                        df.to_csv(file_path, index=False)
                        print(f"👋 Exiting the program. Your notes are saved and **overwrote** '{file_path}'. Goodbye :)")
                    
                    else:
                        # User provided a custom file name or hit Enter

                        # 1. Determine the base path: use user's input or the 'edited' path if input is empty
                        base_path = confirm if confirm.strip() else edited_path
                        
                        # 2. Ensure the path ends with '.csv'
                        if not base_path.lower().endswith(".csv"):
                            output_path = base_path + ".csv"
                        else:
                            output_path = base_path
                        
                        # Save to the determined output path
                        df.to_csv(output_path, index=False)
                        print(f"👋 Exiting the program. Your notes are saved to '{output_path}'. Goodbye :)")
                    
                    break
        
        elif user_input == "new":
            input("Press Enter to save current annotations and load a new CSV file.")
            df.to_csv(file_path, index=False)
            
            # Open a file dialog to select a new csv file
            root = tk.Tk()
            root.withdraw()  # Hide the root window
            file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])

            try:
                df = pd.read_csv(file_path)
                print("✅ New file loaded successfully!\n")
            except FileNotFoundError:
                print("❌ The file was not found. Please check the path and try again.")
                exit()
            except Exception as e:
                print(f"❌ An error occurred while opening the file: {e}")
                exit()

            # Re-initialize for new file
            print("Available columns:")
            print(df.columns.tolist())
            column_name = input("\nWhich column do you want to investigate? ")

            if "user_label" not in df.columns:
                df["user_label"] = ""
            
            # Re-run the annotation setup to get new labels if needed
            print("\n--- Annotation Mode Reloaded ---")
            labels_input = input("Enter new labels separated by a comma (e.g., 'positive,negative,neutral'): ")
            labels = [label.strip() for label in labels_input.split(',') if label.strip()]
            
            if not labels:
                print("❌ No valid labels entered. Exiting.")
                exit()
            
            label_map = {str(i + 1): label for i, label in enumerate(labels)}
            annotation_instructions = [
                f"  - Press '{key}' for '{label}'" for key, label in label_map.items()
            ]
            
            available_indices = list(range(len(df)))
            random.shuffle(available_indices)
            current_index_pos = 0
            
            continue # Skip to the start of the new file's annotation loop

        elif user_input == "back":
            current_index_pos -= 1
            if current_index_pos < 0:
                current_index_pos = 0 # Stay at the beginning
            continue # Go to next loop iteration
        
        # Correctly handles the Skip (Enter key)
        elif not user_input:
            print("⏭️ Skipping entry.")
            input("Press Enter to continue...")
            current_index_pos += 1 # Move to the next entry
            
        # Check if the input is one of the valid annotation keys
        elif user_input in label_map:
            label = label_map[user_input]
            df.at[df_index, "user_label"] = label
            print(f"✅ Annotated as: {label}")
            input("Press Enter to continue...")
            current_index_pos += 1
            
        else:
            print("❌ Invalid input. Please try again.")
            input("Press Enter to continue...")
            # Do not increment current_index_pos, stay on the current item
            continue
            
    else:
        # Loop finished
        df.to_csv(file_path, index=False)
        print("\n\n\n\n✅ End of all entries reached. All annotations are saved. Goodbye :)")


# ----------------------------------------------------------------------

# --- Browsing Mode Implementation ---
elif mode == 'browse':
    # Step 4: Iterate through entries
    print(f"\nExploring column: {column_name}\n")
    index = 0

    # Ensure "user_notes" column exists before loop starts
    if "user_notes" not in df.columns:
        df["user_notes"] = ""

    while index < len(df):
        clear_screen()  # ✅ this clears the screen each time
        print("--- Browsing Mode ---")
        print(f"[{index+1}/{len(df)}] {df[column_name].iloc[index]}")
        
        # Show existing note if any
        current_note = df["user_notes"].iloc[index]
        if current_note:
            print(f"📝 Existing note: {current_note}")
        
        # Cleaned up prompt to be more concise
        user_input = input(
            "\n"
            "\n"
            "You have the following options: \n"
            "\n"
            "Press Enter for next entry, \n"
            "Type 'back' for previous entry, \n"
            "Type 'check' to view another column in the same row, \n"
            "Type 'new' to input a new CSV file, \n"
            "Type 'note' to add a note, \n"
            "Type 'exit' to save all notes and quit.\n" 
        )
        
        if user_input.lower() == "exit":
                    # Determine the default 'edited' file path
                    edited_path = file_path.replace(".csv", "_edited.csv")
                    
                    print(f"\n\nYou are about to save your work.")
                    print(f"Option 1: Overwrite original file (by typing 'yes').")
                    print(f"Option 2: Save as new file (e.g., '{edited_path}').")

                    confirm = input("\nType 'yes' to overwrite, or enter a new file name: ")
                    
                    if confirm.lower() == "yes":
                        # User chose to OVERWRITE the original file
                        df.to_csv(file_path, index=False)
                        print(f"👋 Exiting the program. Your notes are saved and **overwrote** '{file_path}'. Goodbye :)")
                    
                    else:
                        # User provided a custom file name or hit Enter

                        # 1. Determine the base path: use user's input or the 'edited' path if input is empty
                        base_path = confirm if confirm.strip() else edited_path
                        
                        # 2. Ensure the path ends with '.csv'
                        if not base_path.lower().endswith(".csv"):
                            output_path = base_path + ".csv"
                        else:
                            output_path = base_path
                        
                        # Save to the determined output path
                        df.to_csv(output_path, index=False)
                        print(f"👋 Exiting the program. Your notes are saved to '{output_path}'. Goodbye :)")
                    
                    break
        
        elif user_input.lower() == "back":
            index -= 1
            if index < 0:
                index = 0
        
        elif user_input.lower() == "new":
            input("Press Enter to save current notes and load a new CSV file.")
            df.to_csv(file_path, index=False)
            
            # Open a file dialog to select a new csv file
            root = tk.Tk()
            root.withdraw()  # Hide the root window
            file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])

            try:
                df = pd.read_csv(file_path)
                print("✅ New file loaded successfully!\n")
            except FileNotFoundError:
                print("❌ The file was not found. Please check the path and try again.")
                exit()
            except Exception as e:
                print(f"❌ An error occurred while opening the file: {e}")
                exit()

            # Step 2: Show available columns
            print("Available columns:")
            print(df.columns.tolist())
            
            # Step 3: Ask for column name
            column_name = input("\nWhich column do you want to investigate? ")

            if "user_notes" not in df.columns:
                df["user_notes"] = ""
            index = 0
        
        elif user_input.lower() == "note":
            note = input("🗒️ What note would you like to add? ")
            df.at[index, "user_notes"] = note
            print("✅ Note added.")
            input("Press Enter to continue...")
            index += 1
        
        elif user_input.lower() == "check":
            # Display all columns
            print("\nAvailable columns:")
            print(df.columns.tolist())
            context_column = input("Enter the name of the column you want to check: ")
            if context_column in df.columns:
                print("\n\n")
                print(f"Context from column '{context_column}': {df[context_column].iloc[index]}")
                input("Press Enter to continue...")
            else:
                print(f"❌ Column '{context_column}' does not exist.")

        # Handles empty input (Enter) and any other non-command input as next
        else:
            index += 1
    else:
        df.to_csv(file_path, index=False)
        print("\n\n\n\n✅ End of column reached. All notes are saved. Goodbye :)")