
try:
    with open('build_log_stacktrace.txt', 'r', encoding='utf-8', errors='replace') as f:
        print(f.read())
except Exception as e:
    print(e)
