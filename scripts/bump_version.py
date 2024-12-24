import re
from pathlib import Path

def bump_version(version_type='patch'):
    version_file = Path('version.py')
    content = version_file.read_text()
    
    # Extract current version
    match = re.search(r'VERSION = "(\d+)\.(\d+)\.(\d+)"', content)
    if not match:
        raise ValueError("Version not found in version.py")
    
    major, minor, patch = map(int, match.groups())
    
    # Bump version according to type
    if version_type == 'major':
        major += 1
        minor = 0
        patch = 0
    elif version_type == 'minor':
        minor += 1
        patch = 0
    else:  # patch
        patch += 1
    
    new_version = f'{major}.{minor}.{patch}'
    new_content = re.sub(
        r'VERSION = "\d+\.\d+\.\d+"',
        f'VERSION = "{new_version}"',
        content
    )
    
    # Write new version
    version_file.write_text(new_content)
    print(f"Version bumped to {new_version}")
    return new_version

if __name__ == '__main__':
    import sys
    version_type = sys.argv[1] if len(sys.argv) > 1 else 'patch'
    bump_version(version_type) 