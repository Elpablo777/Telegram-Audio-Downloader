import subprocess
import json
import sys
from pathlib import Path

def check_dependencies():
    """Check for outdated and potentially insecure dependencies."""
    print("🔍 Checking for outdated dependencies...")
    try:
        # Get list of outdated packages
        result = subprocess.run(
            [sys.executable, "-m", "pip", "list", "--outdated", "--format=json"],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print("❌ Error checking for outdated packages:")
            print(result.stderr)
            return
            
        outdated = json.loads(result.stdout) if result.stdout.strip() else []
        
        if not outdated:
            print("✅ All dependencies are up to date.")
            return
            
        print(f"\n⚠️  Found {len(outdated)} outdated packages:")
        for pkg in outdated:
            print(f"\n📦 {pkg['name']}")
            print(f"   Current: {pkg['version']}")
            print(f"   Latest:  {pkg['latest_version']}")
            print(f"   Type:    {pkg.get('installer', 'pip')}")
            
    except Exception as e:
        print(f"❌ Error during dependency check: {str(e)}")

def check_secrets():
    """Simple check for common secrets in the codebase."""
    print("\n🔍 Checking for potential secrets in code...")
    try:
        # Common secret patterns to check for
        secret_patterns = [
            r'[a-zA-Z0-9]{24,}',  # API keys
            r'sk_live_[a-zA-Z0-9]{24,}',  # Stripe secret key
            r'AKIA[0-9A-Z]{16}',  # AWS Access Key ID
            r'[0-9a-zA-Z/+]{40}',  # GitHub secret
            r'xoxb-[0-9a-zA-Z-]+',  # Slack bot token
            r'password[\s=:"\']+[^\s"\']+',  # Hardcoded passwords
        ]
        
        # Check common file types
        code_files = list(Path('.').rglob('*.py')) + \
                    list(Path('.').rglob('*.yml')) + \
                    list(Path('.').rglob('*.yaml')) + \
                    list(Path('.').rglob('*.json'))
        
        secrets_found = False
        for file in code_files:
            try:
                content = file.read_text(encoding='utf-8', errors='ignore')
                for pattern in secret_patterns:
                    if not content:
                        continue
                    matches = re.finditer(pattern, content)
                    for match in matches:
                        if not secrets_found:
                            print("\n⚠️  Potential secrets found:")
                            secrets_found = True
                        print(f"\n🔑 Found in {file}")
                        print(f"   Match: {match.group(0)[:50]}...")
                        # Show some context
                        start = max(0, match.start() - 20)
                        end = min(len(content), match.end() + 20)
                        context = content[start:end].replace('\n', ' ').strip()
                        print(f"   Context: ...{context}...")
            except Exception as e:
                print(f"  ⚠️  Error scanning {file}: {str(e)}")
                
        if not secrets_found:
            print("✅ No obvious secrets found in code.")
            
    except Exception as e:
        print(f"❌ Error during secrets check: {str(e)}")

def main():
    print("\n🔒 Basic Security Check 🔒")
    print("======================\n")
    
    check_dependencies()
    check_secrets()
    
    print("\n✅ Security check completed.\n")

if __name__ == "__main__":
    import re
    main()
