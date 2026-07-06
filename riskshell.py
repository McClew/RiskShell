import os
import sys
from app.shell import RiskShell

def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')

    # Resolve absolute path to the app directory
    base_dir = os.path.dirname(os.path.abspath(__file__))
    app_dir = os.path.join(base_dir, 'app')
    
    # Instantiate and execute the shell
    shell = RiskShell(app_dir)
    
    try:
        shell.cmdloop()
    except KeyboardInterrupt:
        print("\n\nProgramme interrupted by user. Exiting Risk Assessment CLI. Security posture analysis complete.\n")
        sys.exit(0)
    except Exception as e:
        print(f"\nCritical system error encountered: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
