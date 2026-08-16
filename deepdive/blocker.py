#!/usr/bin/env python3
import sys
import os

HOSTS_FILE = "/etc/hosts"
BLOCK_MARKER_START = "# --- DEEP DIVE SUBMERGE BLOCKER START ---"
BLOCK_MARKER_END = "# --- DEEP DIVE SUBMERGE BLOCKER END ---"

def get_hosts_content():
    try:
        with open(HOSTS_FILE, 'r') as f:
            return f.read()
    except FileNotFoundError:
        return ""

def write_hosts_content(content):
    with open(HOSTS_FILE, 'w') as f:
        f.write(content)

def remove_deepdive_blocks(content):
    lines = content.split('\n')
    new_lines = []
    in_block = False
    for line in lines:
        if line.strip() == BLOCK_MARKER_START:
            in_block = True
            continue
        if line.strip() == BLOCK_MARKER_END:
            in_block = False
            continue
        if not in_block:
            new_lines.append(line)
    return '\n'.join(new_lines)

def block_domains(domains):
    if not domains:
        return
        
    content = get_hosts_content()
    # Always clean up existing blocks first to avoid duplicates
    clean_content = remove_deepdive_blocks(content)
    
    if not clean_content.endswith('\n'):
        clean_content += '\n'
        
    block_lines = [BLOCK_MARKER_START]
    for d in domains:
        d = d.strip()
        if d:
            block_lines.append(f"127.0.0.1\t{d}")
            block_lines.append(f"127.0.0.1\twww.{d}")
            block_lines.append(f"::1\t{d}")
            block_lines.append(f"::1\twww.{d}")
    block_lines.append(BLOCK_MARKER_END)
    block_lines.append("") # trailing newline
    
    final_content = clean_content + '\n'.join(block_lines)
    write_hosts_content(final_content)

def unblock_domains():
    content = get_hosts_content()
    clean_content = remove_deepdive_blocks(content)
    write_hosts_content(clean_content)

def install_polkit():
    script_path = os.path.abspath(__file__)
    # We use sudoers.d because pkexec does not reliably grant passwordless execution to interpreted scripts
    sudoers_content = f"ALL ALL=(root) NOPASSWD: /usr/bin/python3 {script_path} *\n"
    rule_path = "/etc/sudoers.d/99-deepdive-blocker"
    
    os.makedirs("/etc/sudoers.d", exist_ok=True)
    with open(rule_path, "w") as f:
        f.write(sudoers_content)
        
    os.chmod(rule_path, 0o440)
        
    os.chmod(script_path, 0o755)

def main():
    if os.geteuid() != 0:
        print("This script must be run as root.")
        sys.exit(1)

    if len(sys.argv) < 2:
        print("Usage: python3 blocker.py [block|unblock] [domains_comma_separated]")
        sys.exit(1)

    action = sys.argv[1]

    if action == "block":
        if len(sys.argv) < 3:
            print("Provide domains to block.")
            sys.exit(1)
        domains = sys.argv[2].split(',')
        block_domains(domains)
        print("Domains blocked.")
    elif action == "unblock":
        unblock_domains()
        print("Domains unblocked.")
    elif action == "install":
        install_polkit()
        print("Polkit rule installed.")
    else:
        print("Unknown action.")
        sys.exit(1)

if __name__ == "__main__":
    main()
