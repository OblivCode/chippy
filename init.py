import sys, asyncio
import time
from threading import Thread
import pygame
from queue import Queue
import sdl2.ext
import numpy as np
from classes import Chip8, Screen 
resolution = (64,32) #wxh colsxrows
factory = sdl2.ext.SpriteFactory(sdl2.ext.SOFTWARE)
sprite = factory.from_image("C:\\Users\\Eman\\Pictures\\Beast_Gohan_Powers_Up.webp")

fontset = np.array([
    0xF0, 0x90, 0x90, 0x90, 0xF0, # 0
    0x20, 0x60, 0x20, 0x20, 0x70, # 1
    0xF0, 0x10, 0xF0, 0x80, 0xF0, # 2
    0xF0, 0x10, 0xF0, 0x10, 0xF0, # 3
    0x90, 0x90, 0xF0, 0x10, 0x10, # 4
    0xF0, 0x80, 0xF0, 0x10, 0xF0, # 5
    0xF0, 0x80, 0xF0, 0x90, 0xF0, # 6
    0xF0, 0x10, 0x20, 0x40, 0x40, # 7
    0xF0, 0x90, 0xF0, 0x90, 0xF0, # 8
    0xF0, 0x90, 0xF0, 0x10, 0xF0, # 9
    0xF0, 0x90, 0xF0, 0x90, 0x90, # A
    0xE0, 0x90, 0xE0, 0x90, 0xE0, # B
    0xF0, 0x80, 0x80, 0x80, 0xF0, # C
    0xE0, 0x90, 0x90, 0x90, 0xE0, # D
    0xF0, 0x80, 0xF0, 0x80, 0xF0, # E
    0xF0, 0x80, 0xF0, 0x80, 0x80  # F
], dtype=np.uint8)

video_scale = 3
delay_time = 500 #delay
rom_file = ""
std_queue = Queue()
#code



#screen = Screen.Screen("Chip8", resolution)
def EventHandler(event: pygame.event.Event):
    if event.type == pygame.QUIT:
        pygame.quit()
        sys.exit()
    elif event.type == pygame.KEYDOWN:
        key = event.key
        print(key)

pygame.init()

display = Screen((64,32))
display.start()

chip = Chip8(delay_time)
chip.LoadFontset(fontset)
chip.LoadROM(rom_file)


def main():
    counter = 0
    chip_cycle_time = 200000
    video_update_time = 400000
    while True:
        for event in pygame.event.get():
            EventHandler(event)
        counter += 1
        if counter/chip_cycle_time == round(counter/chip_cycle_time):
            chip.Cycle()
        if counter/video_update_time == round(counter/video_update_time):
            counter = 0
            video_buffer = chip.display_memory
            display.Update(video_buffer)
        
main()

# run screen
#processor = sdl2.ext.TestEventProcessor()
#processor.run(window)