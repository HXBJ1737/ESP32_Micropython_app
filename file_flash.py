import micropython
import esp
import os

print(esp.flash_size()/1024/1024)
print(micropython.mem_info())
print(os.listdir())