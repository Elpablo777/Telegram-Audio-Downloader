import os
import subprocess

def run_git_command(command):
    """Run a git command and return the output"""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"Success: {command}")
            if result.stdout:
                print(f"Output: {result.stdout}")
        else:
            print(f"Error running: {command}")
            print(f"Error: {result.stderr}")
        return result.returncode == 0
    except Exception as e:
        print(f"Exception running {command}: {e}")
        return False

# Add all changes
print("Adding all changes...")
run_git_command("git add .")

# Commit changes
print("\nCommitting changes...")
run_git_command('git commit -m "Synchronize local changes with GitHub"')

# Push to GitHub
print("\nPushing to GitHub...")
run_git_command("git push origin main")

print("\nDone! Local changes should now be synchronized with GitHub.")