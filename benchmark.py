import psutil

pid = 25436

try:
    process = psutil.Process(pid)
    while True:
       cpu_usage = process.cpu_percent(interval=1)
       memory_usage = process.memory_info().rss / (1024 * 1024)
       print("CPU: {} , RAM: {} MB".format(cpu_usage,memory_usage))
except psutil.NoSuchProcess:
  print(f"Process with PID {pid} not found.")
  exit(1)