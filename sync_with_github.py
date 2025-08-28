import os
import subprocess

def run_git_command(command_args):
    """Run a git command and return the output"""
    try:
        # Use shell=False and pass arguments as a list to prevent shell injection
        result = subprocess.run(command_args, shell=False, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"Success: {' '.join(command_args)}")
            if result.stdout:
                print(f"Output: {result.stdout}")
        else:
            print(f"Error running: {' '.join(command_args)}")
            print(f"Error: {result.stderr}")
        return result.returncode == 0
    except Exception as e:
        print(f"Exception running {' '.join(command_args)}: {e}")
        return False

# Add all changes
print("Adding all changes...")
run_git_command(["git", "add", "."])

# Commit changes
print("\nCommitting changes...")
run_git_command(["git", "commit", "-m", "Synchronize local changes with GitHub"])

# Push to GitHub
print("\nPushing to GitHub...")
run_git_command(["git", "push", "origin", "main"])

print("\nDone! Local changes should now be synchronized with GitHub.")