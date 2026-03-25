import pyautogui as pg 
from time import sleep


sleep(6)

for i in range(5):
    sleep(0.5)
    pg.hotkey('ctrl', 'shift', 'e')
    sleep(0.5)
    pg.press('down')
    sleep(0.5)
    pg.press('enter')
    sleep(0.5)
    pg.hotkey('ctrl', 'shift', 'e')
    sleep(0.5)
    pg.hotkey('fn', 'f2')
    sleep(0.5)
    pg.hotkey('ctrl', 'a')
    sleep(0.5)
    pg.hotkey('ctrl', 'c')
    sleep(0.5)
    pg.hotkey('alt', 'tab')
    sleep(0.5)
    pg.click(142, 247)
    sleep(0.5)
    pg.hotkey('ctrl', 'v')
    sleep(1)
    pg.press('enter')
    sleep(2)
    pg.hotkey('alt', 'tab')
    sleep(0.5)
    pg.click(442, 647)
    sleep(0.5)
    pg.hotkey('ctrl', 'a')
    sleep(0.5)
    pg.hotkey('ctrl', 'c')
    sleep(1)
    pg.hotkey('alt', 'tab')
    sleep(1.5)
    pg.click(542, 647)
    sleep(1)
    pg.hotkey('ctrl', 'a')
    sleep(0.5)
    pg.press('backspace')
    sleep(1.5)
    pg.click(542, 647)
    sleep(1)
    pg.hotkey('ctrl', 'v')
    sleep(1)
    pg.hotkey('alt', 'tab')
    sleep(0.5)
    pg.click(442, 647)

# import pyautogui
# import time

# print("Move your mouse to the desired location...")
# print("Recording coordinates in 3 seconds...")

# # Wait for 3 seconds
# time.sleep(3)

# # Get current mouse position
# x, y = pyautogui.position()

# # Print coordinates
# print(f"Coordinates: ({x}, {y})")
# print(f"X: {x}, Y: {y}")